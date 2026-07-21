#!/usr/bin/env python3
"""Build common-calendar forward evaluation windows whose assignment ignores gt.

This replaces frequency-specific row-quantile cutoffs for the confirmatory design.
The training side expands and the forward test tail contracts, so the five
checkpoints are dependent: 80% is primary and the other four are sensitivity
windows. Positive-event counts were inspected during a disclosed Gate 0 pilot;
all five assignments are now retained and all five windows must be reported.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import pandas as pd


FREQUENCIES = ("25S", "15S", "5S")
FRACTIONS = (0.40, 0.50, 0.60, 0.70, 0.80)
PRIMARY_FRACTION = 0.80


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_frequency(path: Path) -> pd.DataFrame:
    return pd.read_csv(
        path,
        usecols=["date", "pump_index", "symbol", "gt"],
        parse_dates=["date"],
    ).reset_index(names="source_row")


def build_canonical_groups(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    common_ids = set.intersection(
        *(set(frame["pump_index"].unique()) for frame in frames.values())
    )
    if not common_ids:
        raise ValueError("No common event ids across frequencies")

    per_frequency = {}
    for frequency, frame in frames.items():
        group = (
            frame.loc[frame["pump_index"].isin(common_ids)]
            .groupby("pump_index", sort=True)
            .agg(symbol=("symbol", "first"), start=("date", "min"), end=("date", "max"))
        )
        per_frequency[frequency] = group

    records = []
    for event_id in sorted(common_ids):
        symbols = {per_frequency[f].loc[event_id, "symbol"] for f in frames}
        if len(symbols) != 1:
            raise AssertionError(f"Symbol mismatch for event id {event_id}: {symbols}")
        starts = [per_frequency[f].loc[event_id, "start"] for f in frames]
        ends = [per_frequency[f].loc[event_id, "end"] for f in frames]
        canonical_start = min(starts)
        canonical_end = max(ends)
        records.append(
            {
                "pump_index": int(event_id),
                "symbol": next(iter(symbols)),
                "canonical_start": canonical_start,
                "canonical_end": canonical_end,
                "canonical_anchor": canonical_start + (canonical_end - canonical_start) / 2,
                "cross_frequency_start_jitter_seconds": float(
                    (max(starts) - min(starts)).total_seconds()
                ),
                "cross_frequency_end_jitter_seconds": float(
                    (max(ends) - min(ends)).total_seconds()
                ),
            }
        )
    return pd.DataFrame(records).sort_values(
        ["canonical_anchor", "pump_index"], kind="mergesort"
    ).reset_index(drop=True)


def common_cutoff(canonical_groups: pd.DataFrame, fraction: float) -> pd.Timestamp:
    if not 0 < fraction < 1:
        raise ValueError("fraction must lie strictly between zero and one")
    index = int(len(canonical_groups) * fraction)
    if index <= 0 or index >= len(canonical_groups):
        raise ValueError("fraction creates an empty side")
    left = pd.Timestamp(canonical_groups.iloc[index - 1]["canonical_anchor"])
    right = pd.Timestamp(canonical_groups.iloc[index]["canonical_anchor"])
    if not left <= right:
        raise AssertionError("canonical event order is not monotonic")
    return left + (right - left) / 2


def assign_groups(canonical_groups: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    assigned = canonical_groups.copy()
    assigned["partition"] = "purged"
    assigned.loc[assigned["canonical_end"] < cutoff, "partition"] = "train"
    assigned.loc[assigned["canonical_start"] >= cutoff, "partition"] = "test"
    if not set(assigned["partition"]).issubset({"train", "test", "purged"}):
        raise AssertionError("Unexpected partition value")
    return assigned


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()

    output_root = args.output_root.resolve()
    if output_root.exists() and any(output_root.iterdir()):
        raise SystemExit(f"Refusing non-empty output directory: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)

    frames = {}
    inputs = []
    for frequency in FREQUENCIES:
        path = args.data_root.resolve() / f"features_{frequency}.csv.gz"
        frames[frequency] = load_frequency(path)
        inputs.append(
            {
                "frequency": frequency,
                "filename": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )

    canonical = build_canonical_groups(frames)
    canonical.to_csv(output_root / "canonical_common_event_manifest.csv", index=False)
    rows = []
    common_ids = set(canonical["pump_index"])
    excluded_rows = []
    for frequency, frame in frames.items():
        excluded = frame.loc[~frame["pump_index"].isin(common_ids)]
        for event_id, group in excluded.groupby("pump_index", sort=True):
            excluded_rows.append(
                {
                    "frequency": frequency,
                    "pump_index": int(event_id),
                    "symbol": group["symbol"].iloc[0],
                    "rows": int(len(group)),
                    "start": group["date"].min().isoformat(),
                    "end": group["date"].max().isoformat(),
                    "positive_rows_post_design_pilot_diagnostic": int(group["gt"].sum()),
                }
            )
    pd.DataFrame(excluded_rows).to_csv(
        output_root / "excluded_noncommon_event_manifest.csv", index=False
    )

    for fraction in FRACTIONS:
        cutoff = common_cutoff(canonical, fraction)
        assigned = assign_groups(canonical, cutoff)
        assignment = assigned.set_index("pump_index")["partition"]
        assigned.to_csv(
            output_root / f"event_partition_{int(fraction * 100):02d}.csv", index=False
        )

        for frequency, frame in frames.items():
            included = frame.loc[frame["pump_index"].isin(common_ids)].copy()
            row_partition = included["pump_index"].map(assignment)
            train = included.loc[row_partition == "train"]
            test = included.loc[row_partition == "test"]
            purged = included.loc[row_partition == "purged"]
            if train.empty or test.empty:
                raise AssertionError("empty train or test side")
            strict_time_forward = bool(train["date"].max() < test["date"].min())
            if not strict_time_forward:
                raise AssertionError("strict common-calendar time invariant failed")
            train_ids = set(train["pump_index"].unique())
            test_ids = set(test["pump_index"].unique())
            event_overlap = len(train_ids & test_ids)
            if event_overlap:
                raise AssertionError("train/test event overlap")

            group_label = included.groupby("pump_index")["gt"].max()
            positive_assignment = group_label.index.to_series().map(assignment)
            rows.append(
                {
                    "frequency": frequency,
                    "event_fraction": fraction,
                    "role": "primary" if fraction == PRIMARY_FRACTION else "sensitivity",
                    "common_calendar_cutoff": cutoff.isoformat(),
                    "train_rows": int(len(train)),
                    "test_rows": int(len(test)),
                    "purged_rows": int(len(purged)),
                    "excluded_noncommon_rows": int(
                        (~frame["pump_index"].isin(common_ids)).sum()
                    ),
                    "train_events": int((assigned["partition"] == "train").sum()),
                    "test_events": int((assigned["partition"] == "test").sum()),
                    "purged_events": int((assigned["partition"] == "purged").sum()),
                    "train_positive_events_post_design_pilot_diagnostic": int(
                        group_label.loc[positive_assignment == "train"].sum()
                    ),
                    "test_positive_events_post_design_pilot_diagnostic": int(
                        group_label.loc[positive_assignment == "test"].sum()
                    ),
                    "purged_positive_events_post_design_pilot_diagnostic": int(
                        group_label.loc[positive_assignment == "purged"].sum()
                    ),
                    "event_overlap": event_overlap,
                    "strict_time_forward": strict_time_forward,
                    "assignment_rule_references_gt": False,
                    "windows_are_independent": False,
                }
            )

    pd.DataFrame(rows).to_csv(
        output_root / "common_calendar_forward_windows.csv", index=False
    )
    pd.DataFrame(inputs).to_csv(output_root / "input_manifest.csv", index=False)
    design = {
        "frequencies": FREQUENCIES,
        "common_event_count": int(len(canonical)),
        "fractions": FRACTIONS,
        "primary_fraction": PRIMARY_FRACTION,
        "cutoff_basis": (
            "rank of common event interval anchors; assignment rules do not reference gt"
        ),
        "pilot_label_inspection_disclosure": (
            "Positive-event counts were inspected during Gate 0 feasibility. All five "
            "windows, including the 80% primary, are now retained; none may be removed "
            "based on labels or performance. This is not claimed as preregistration or "
            "label-blind design."
        ),
        "dependence_rule": (
            "Training windows expand while forward test tails contract and remain nested. "
            "Report each separately; do not pool them or treat them as independent replicates."
        ),
        "cross_frequency_rule": (
            "Use identical calendar cutoffs and the intersection event set. AP remains "
            "prevalence-sensitive and is not directly compared across frequencies."
        ),
    }
    (output_root / "design.json").write_text(
        json.dumps(design, indent=2), encoding="utf-8"
    )
    run_metadata = {
        "command": " ".join(sys.argv),
        "python": sys.version,
        "platform": platform.platform(),
        "pandas": pd.__version__,
        "script": str(Path(__file__).resolve()),
        "script_sha256": sha256(Path(__file__).resolve()),
    }
    (output_root / "run_metadata.json").write_text(
        json.dumps(run_metadata, indent=2), encoding="utf-8"
    )
    output_records = []
    for path in sorted(output_root.iterdir()):
        if path.is_file() and path.name != "output_manifest.csv":
            output_records.append(
                {"filename": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
            )
    pd.DataFrame(output_records).to_csv(output_root / "output_manifest.csv", index=False)
    print(json.dumps(design, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
