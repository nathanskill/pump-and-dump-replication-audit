#!/usr/bin/env python3
"""Gate-0 structural audit for REF-2026-016.

The forward partition is built from source-row id, event id, and timestamp only.
Outcome labels are attached afterwards solely for feasibility diagnostics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


DEFAULT_FRACTIONS = (0.40, 0.50, 0.60, 0.70, 0.80)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_label_free_partition(
    label_free: pd.DataFrame, fraction: float
) -> tuple[pd.Timestamp, pd.DataFrame, pd.Series]:
    allowed = {"source_row", "pump_index", "date"}
    if set(label_free.columns) != allowed:
        raise ValueError(f"Partition input must be exactly {sorted(allowed)}")
    if not 0 < fraction < 1:
        raise ValueError("fraction must lie strictly between zero and one")

    ordered = label_free["date"].sort_values(kind="mergesort").reset_index(drop=True)
    cutoff_index = int(len(ordered) * fraction)
    if cutoff_index <= 0 or cutoff_index >= len(ordered):
        raise ValueError("cutoff creates an empty side")
    cutoff = pd.Timestamp(ordered.iloc[cutoff_index])

    groups = (
        label_free.groupby("pump_index", sort=True)["date"]
        .agg(group_min_date="min", group_max_date="max", n_rows="size")
        .reset_index()
    )
    groups["partition"] = "purged"
    groups.loc[groups["group_max_date"] < cutoff, "partition"] = "train"
    groups.loc[groups["group_min_date"] >= cutoff, "partition"] = "test"
    partition_map = groups.set_index("pump_index")["partition"]
    rows = label_free["pump_index"].map(partition_map)

    train_groups = set(groups.loc[groups["partition"] == "train", "pump_index"])
    test_groups = set(groups.loc[groups["partition"] == "test", "pump_index"])
    if train_groups & test_groups:
        raise AssertionError("event groups overlap across train and test")

    train_dates = label_free.loc[rows == "train", "date"]
    test_dates = label_free.loc[rows == "test", "date"]
    if train_dates.empty or test_dates.empty:
        raise AssertionError("forward partition has an empty train or test side")
    if not train_dates.max() < test_dates.min():
        raise AssertionError("strict row-time-forward invariant failed")

    return cutoff, groups, rows


def audit_frequency(path: Path, frequency: str, fractions: tuple[float, ...]):
    frame = pd.read_csv(
        path,
        usecols=["date", "pump_index", "gt"],
        parse_dates=["date"],
    ).reset_index(names="source_row")
    group_labels = frame.groupby("pump_index", sort=True)["gt"].max()
    group_dates = frame.groupby("pump_index", sort=True)["date"].agg(["min", "max"])
    group_hours = (group_dates["max"] - group_dates["min"]).dt.total_seconds() / 3600

    summary = {
        "frequency": frequency,
        "rows": int(len(frame)),
        "events": int(frame["pump_index"].nunique()),
        "positive_rows": int(frame["gt"].sum()),
        "positive_events": int(group_labels.sum()),
        "min_date": frame["date"].min().isoformat(),
        "max_date": frame["date"].max().isoformat(),
        "event_window_hours_min": float(group_hours.min()),
        "event_window_hours_median": float(group_hours.median()),
        "event_window_hours_max": float(group_hours.max()),
    }

    feasibility: list[dict[str, object]] = []
    label_free = frame[["source_row", "pump_index", "date"]].copy()
    for fraction in fractions:
        cutoff, groups, row_partition = build_label_free_partition(label_free, fraction)
        group_partition = groups.set_index("pump_index")["partition"]
        positive_event_partition = group_labels.index.to_series().map(group_partition)
        record = {
            "frequency": frequency,
            "row_cut_fraction": fraction,
            "cutoff": cutoff.isoformat(),
            "train_rows": int((row_partition == "train").sum()),
            "test_rows": int((row_partition == "test").sum()),
            "purged_rows": int((row_partition == "purged").sum()),
            "train_events": int((groups["partition"] == "train").sum()),
            "test_events": int((groups["partition"] == "test").sum()),
            "purged_events": int((groups["partition"] == "purged").sum()),
            "train_positive_events_post_split_diagnostic": int(
                group_labels.loc[positive_event_partition == "train"].sum()
            ),
            "test_positive_events_post_split_diagnostic": int(
                group_labels.loc[positive_event_partition == "test"].sum()
            ),
            "purged_positive_events_post_split_diagnostic": int(
                group_labels.loc[positive_event_partition == "purged"].sum()
            ),
            "event_overlap": 0,
            "strict_time_forward": True,
            "split_uses_gt": False,
        }
        feasibility.append(record)
    return summary, feasibility


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument(
        "--frequencies", nargs="+", default=["25S", "15S", "5S"]
    )
    args = parser.parse_args()

    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, object]] = []
    feasibility: list[dict[str, object]] = []
    inputs: list[dict[str, object]] = []

    for frequency in args.frequencies:
        path = args.data_root.resolve() / f"features_{frequency}.csv.gz"
        if not path.exists():
            raise FileNotFoundError(path)
        summary, rows = audit_frequency(path, frequency, DEFAULT_FRACTIONS)
        summaries.append(summary)
        feasibility.extend(rows)
        inputs.append(
            {
                "frequency": frequency,
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )

    (output_root / "structure_summary.json").write_text(
        json.dumps(summaries, indent=2), encoding="utf-8"
    )
    pd.DataFrame(feasibility).to_csv(
        output_root / "forward_cutoff_feasibility.csv", index=False
    )
    pd.DataFrame(inputs).to_csv(output_root / "input_manifest.csv", index=False)
    print(json.dumps(summaries, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

