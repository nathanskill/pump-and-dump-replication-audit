#!/usr/bin/env python3
"""Formal S2 common-calendar forward runs under frozen protocol v0.2.

Protocol freeze commit: 23089ceebd93eed421b8a2a710135851dcab536e (v0.2).
Amendment A1 (author-query waiver, claim boundaries only): d52f8ae.

Design, all frozen before these runs:
- three frequencies x five expanding common-calendar checkpoints from the v3
  label-free partition manifests; the 80% checkpoint is primary and the
  40/50/60/70% checkpoints are dependent sensitivity windows;
- released-code Random Forest (n_estimators=200, max_depth=5,
  min_samples_leaf=1, random_state=1);
- thresholds: replication anchor tau=0.5, plus tau* selected only inside the
  outer-training window via a label-free expanding-time inner split
  (fraction 0.8) and chunk-level F1 with ties resolving to the higher
  threshold. Declared fallback: if the inner validation tail contains no
  positive row, tau* falls back to 0.5 and the run is flagged;
- row-level outcomes: Average Precision (primary), ROC-AUC, prevalence,
  precision/recall/F1 at both thresholds;
- event-level outcomes: the frozen `event_metrics` specification on eligible
  held-out events, reported at both thresholds with event-cluster bootstrap
  intervals (n_boot=2000, seed=20260722) for EDR_exact, EDR@120s and the
  benchmark-negative episode mean;
- purged events are excluded from training and testing; every output is
  non-overwriting and hashed; per-row predictions stay local (gitignored).

These runs measure benchmark-faithful quantities on the event-centred public
matrices only. No real-market prevalence, daily false alerts, deployment
specificity or analyst workload conclusions are permitted.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]

PROTOCOL_FREEZE_COMMIT = "23089ceebd93eed421b8a2a710135851dcab536e"
AMENDMENT_A1_COMMIT = "d52f8ae"

FREQUENCIES = ("25S", "15S", "5S")
FRACTIONS = (0.40, 0.50, 0.60, 0.70, 0.80)
PRIMARY_FRACTION = 0.80
INNER_TRAIN_FRACTION = 0.80
BOOT_N = 2000
BOOT_SEED = 20260722

RF_PARAMS = {
    "n_estimators": 200,
    "max_depth": 5,
    "min_samples_leaf": 1,
    "random_state": 1,
}

FEATURES = [
    "std_rush_order",
    "avg_rush_order",
    "std_trades",
    "std_volume",
    "avg_volume",
    "std_price",
    "avg_price",
    "avg_price_max",
    "hour_sin",
    "hour_cos",
    "minute_sin",
    "minute_cos",
]

PARTITION_DIR = ROOT / "artifacts" / "gate0_common_calendar_forward_v3_20260721"
DEFAULT_UPSTREAM = ROOT.parent / "tmp/repro_public_20260715/pump-and-dump-dataset"
OUTPUT_ROOT = ROOT / "artifacts" / "formal_forward_v1_20260722"


def load_module(name: str):
    path = ROOT / "src" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


EM = load_module("event_metrics")
STRUCTURE = load_module("audit_structure")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def binary_metrics(y: np.ndarray, predicted: np.ndarray) -> dict:
    tp = int(np.sum(predicted & (y == 1)))
    fp = int(np.sum(predicted & (y == 0)))
    fn = int(np.sum(~predicted & (y == 1)))
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
    }


def event_block(test_frame: pd.DataFrame, scores: np.ndarray, tau: float, bin_seconds: int) -> dict:
    classification = EM.classify_events(test_frame)
    outcomes = []
    score_series = pd.Series(scores, index=test_frame.index)
    for event_id in classification.eligible:
        group = test_frame.loc[test_frame["pump_index"] == event_id]
        outcomes.append(
            EM.score_event(
                group,
                score_series.loc[group.index].to_numpy(),
                tau=tau,
                bin_seconds=bin_seconds,
            )
        )
    summary = EM.summarize_events(outcomes)
    exact_hits = np.array([float(o.exact_hit) for o in outcomes])
    edr120_hits = np.array([float(o.detection_hits[120]) for o in outcomes])
    episodes = np.array(summary.benchmark_negative_episodes_by_event, dtype=float)
    return {
        "n_eligible_test_events": summary.n_eligible,
        "n_no_positive_test_groups": len(classification.no_positive),
        "edr_exact": summary.edr_exact,
        "edr_exact_ci95": EM.cluster_bootstrap_interval(exact_hits, BOOT_N, BOOT_SEED),
        "edr_at": {str(h): v for h, v in summary.edr_at.items()},
        "edr_at_120_ci95": EM.cluster_bootstrap_interval(edr120_hits, BOOT_N, BOOT_SEED),
        "lead_at": {str(h): v for h, v in summary.lead_at.items()},
        "delay_median_s": summary.delay_median,
        "delay_q25_s": summary.delay_q25,
        "delay_q75_s": summary.delay_q75,
        "delay_p90_s": summary.delay_p90,
        "n_detected_within_120s": summary.n_detected_within_delay_horizon,
        "benchmark_negative_mean": summary.benchmark_negative_mean,
        "benchmark_negative_median": summary.benchmark_negative_median,
        "benchmark_negative_mean_ci95": EM.cluster_bootstrap_interval(
            episodes, BOOT_N, BOOT_SEED
        ),
        "per_event": [
            {
                "pump_index": o.pump_index,
                "exact_hit": o.exact_hit,
                "hit_120": o.detection_hits[120],
                "delay_s": o.delay_seconds,
                "benchmark_negative_episodes": o.benchmark_negative_episodes,
                "n_emitted": o.n_emitted,
            }
            for o in outcomes
        ],
    }


TIME_FEATURES = ["hour_sin", "hour_cos", "minute_sin", "minute_cos"]


def run_one(
    frequency: str,
    fraction: float,
    upstream: Path,
    out_root: Path,
    features: list[str] | None = None,
) -> dict:
    features = FEATURES if features is None else features
    bin_seconds = EM.FREQUENCY_BIN_SECONDS[frequency]
    matrix_path = upstream / "labeled_features" / f"features_{frequency}.csv.gz"
    partition_path = PARTITION_DIR / f"event_partition_{int(fraction * 100)}.csv"

    frame = pd.read_csv(
        matrix_path,
        usecols=["date", "pump_index", "gt"] + features,
        parse_dates=["date"],
    )
    partition = pd.read_csv(partition_path)[["pump_index", "partition"]]
    frame = frame.merge(partition, on="pump_index", how="inner")

    train = frame.loc[frame["partition"] == "train"].reset_index(drop=True)
    test = frame.loc[frame["partition"] == "test"].reset_index(drop=True)

    # tau*: label-free expanding-time inner split within the outer train only.
    inner_frame = train[["pump_index", "date"]].reset_index(names="source_row")
    _, _, inner_rows = STRUCTURE.build_label_free_partition(
        inner_frame, INNER_TRAIN_FRACTION
    )
    inner_train_index = inner_frame.loc[inner_rows == "train", "source_row"].to_numpy()
    inner_valid_index = inner_frame.loc[inner_rows == "test", "source_row"].to_numpy()

    x_train = train[features].to_numpy(dtype=np.float64)
    y_train = train["gt"].to_numpy(dtype=int)
    x_test = test[features].to_numpy(dtype=np.float64)
    y_test = test["gt"].to_numpy(dtype=int)

    inner_model = RandomForestClassifier(**RF_PARAMS, n_jobs=-1)
    inner_model.fit(x_train[inner_train_index], y_train[inner_train_index])
    inner_scores = inner_model.predict_proba(x_train[inner_valid_index])[:, 1]
    inner_y = y_train[inner_valid_index]
    tau_star_fallback = False
    if inner_y.sum() == 0:
        tau_star = EM.REPLICATION_ANCHOR_TAU
        tau_table = pd.DataFrame()
        tau_star_fallback = True
    else:
        tau_star, tau_table = EM.select_tau_star(inner_y, inner_scores)

    model = RandomForestClassifier(**RF_PARAMS, n_jobs=-1)
    model.fit(x_train, y_train)
    scores = model.predict_proba(x_test)[:, 1]

    row_metrics = {
        "n_train_rows": int(len(train)),
        "n_test_rows": int(len(test)),
        "n_train_events": int(train["pump_index"].nunique()),
        "n_test_events": int(test["pump_index"].nunique()),
        "test_prevalence": float(y_test.mean()),
        "average_precision": float(average_precision_score(y_test, scores)),
        "roc_auc": (
            float(roc_auc_score(y_test, scores))
            if len(np.unique(y_test)) > 1
            else None
        ),
        "at_tau_anchor": binary_metrics(y_test, scores >= EM.REPLICATION_ANCHOR_TAU),
        "at_tau_star": binary_metrics(y_test, scores >= tau_star),
    }

    result = {
        "frequency": frequency,
        "fraction": fraction,
        "is_primary": fraction == PRIMARY_FRACTION,
        "tau_anchor": EM.REPLICATION_ANCHOR_TAU,
        "tau_star": float(tau_star),
        "tau_star_fallback_no_inner_positives": tau_star_fallback,
        "n_inner_valid_rows": int(len(inner_valid_index)),
        "n_inner_valid_positives": int(inner_y.sum()),
        "row_level": row_metrics,
        "event_level_at_tau_anchor": event_block(
            test, scores, EM.REPLICATION_ANCHOR_TAU, bin_seconds
        ),
        "event_level_at_tau_star": event_block(test, scores, tau_star, bin_seconds),
    }

    out_dir = out_root / f"{frequency}_{int(fraction * 100)}"
    out_dir.mkdir(parents=True, exist_ok=False)
    with (out_dir / "metrics.json").open("w") as handle:
        json.dump(result, handle, indent=2)
    if not tau_table.empty:
        tau_table.to_csv(out_dir / "tau_star_selection_table.csv", index=False)
    predictions = test[["pump_index", "date", "gt"]].assign(score=scores)
    with gzip.open(out_dir / f"predictions_{frequency}_{int(fraction*100)}.csv.gz", "wt") as handle:
        predictions.to_csv(handle, index=False)
    with (out_dir / "input_manifest.json").open("w") as handle:
        json.dump(
            {
                "matrix": f"upstream:labeled_features/{matrix_path.name}",
                "matrix_sha256": sha256(matrix_path),
                "partition": str(partition_path.relative_to(ROOT)),
                "partition_sha256": sha256(partition_path),
            },
            handle,
            indent=2,
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, default=DEFAULT_UPSTREAM)
    parser.add_argument("--frequencies", nargs="*", default=list(FREQUENCIES))
    parser.add_argument("--fractions", nargs="*", type=float, default=list(FRACTIONS))
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument(
        "--drop-time-features",
        action="store_true",
        help="Ablation: drop the four cyclical time-of-day columns "
        "(spec: protocol/formal_cv_and_ablation_spec_v0.1.md)",
    )
    args = parser.parse_args()

    features = (
        [f for f in FEATURES if f not in TIME_FEATURES]
        if args.drop_time_features
        else list(FEATURES)
    )
    args.output_root.mkdir(parents=True, exist_ok=True)
    config = {
        "protocol_freeze_commit": PROTOCOL_FREEZE_COMMIT,
        "amendment_a1_commit": AMENDMENT_A1_COMMIT,
        "rf_params": RF_PARAMS,
        "features": features,
        "ablation_dropped": TIME_FEATURES if args.drop_time_features else [],
        "inner_train_fraction": INNER_TRAIN_FRACTION,
        "tau_star_rule": (
            "chunk-level F1 on label-free expanding-time inner validation within "
            "outer train; candidates = unique inner OOF scores + 0.5; ties -> "
            "higher tau; fallback to 0.5 if the inner tail has no positives"
        ),
        "bootstrap": {"n_boot": BOOT_N, "seed": BOOT_SEED, "cluster": "pump_index"},
        "primary_fraction": PRIMARY_FRACTION,
        "python": platform.python_version(),
        "platform": platform.platform(),
    }
    with (args.output_root / "run_config.json").open("w") as handle:
        json.dump(config, handle, indent=2)

    summary = []
    for frequency in args.frequencies:
        for fraction in args.fractions:
            print(f"[run] {frequency} @ {int(fraction*100)}%", flush=True)
            result = run_one(
                frequency, fraction, args.upstream, args.output_root, features
            )
            row = result["row_level"]
            print(
                f"  AP={row['average_precision']:.4f} "
                f"tau*={result['tau_star']:.3f} "
                f"EDR@120(anchor)={result['event_level_at_tau_anchor']['edr_at']['120']:.3f}",
                flush=True,
            )
            summary.append(
                {
                    "frequency": frequency,
                    "fraction": fraction,
                    "average_precision": row["average_precision"],
                    "tau_star": result["tau_star"],
                    "edr_exact_anchor": result["event_level_at_tau_anchor"]["edr_exact"],
                    "edr_120_anchor": result["event_level_at_tau_anchor"]["edr_at"]["120"],
                    "edr_120_tau_star": result["event_level_at_tau_star"]["edr_at"]["120"],
                }
            )
    pd.DataFrame(summary).to_csv(args.output_root / "summary.csv", index=False)
    print("[done]", flush=True)


if __name__ == "__main__":
    main()
