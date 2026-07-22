#!/usr/bin/env python3
"""Formal S1 (event-exclusive 5-fold) and S0 (row-level 5-fold) comparison runs.

Spec: protocol/formal_cv_and_ablation_spec_v0.1.md (frozen before execution).
Protocol freeze commit: c2736ed36e6a074ded78e916c071d5d396b316c3 (v0.2).

Both families run on the same row universe as S2: rows of the 326 common
events from the v3 partition design, so family differences are attributable
to split logic, not universe composition.

- S1_EVENT_5FOLD: GroupKFold(5) by pump_index; per outer fold, tau*_fold from
  event-grouped GroupKFold(4) inner OOF probabilities (chunk-level F1, ties to
  the higher threshold, fallback 0.5 if no inner positives); pooled OOF AP;
  event outcomes pooled over all eligible events at tau=0.5 and tau*_fold.
- S0_ROW_5FOLD: upstream-style non-shuffled stratified row 5-fold; chunk-level
  metrics only (rows of one event sit on both sides of the split, so event
  detection/delay are not reported).

Benchmark-faithful quantities only; no real-market claims.
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
from sklearn.model_selection import GroupKFold, StratifiedKFold

ROOT = Path(__file__).resolve().parents[1]

PROTOCOL_FREEZE_COMMIT = "c2736ed36e6a074ded78e916c071d5d396b316c3"

FREQUENCIES = ("25S", "15S", "5S")
OUTER_FOLDS = 5
INNER_FOLDS = 4
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
OUTPUT_ROOT = ROOT / "artifacts" / "formal_s1_s0_v1_20260722"


def load_module(name: str):
    path = ROOT / "src" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


EM = load_module("event_metrics")


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
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def load_universe(frequency: str, upstream: Path) -> pd.DataFrame:
    matrix_path = upstream / "labeled_features" / f"features_{frequency}.csv.gz"
    frame = pd.read_csv(
        matrix_path,
        usecols=["date", "pump_index", "gt"] + FEATURES,
        parse_dates=["date"],
    )
    universe = pd.read_csv(PARTITION_DIR / "canonical_common_event_manifest.csv")
    frame = frame.loc[frame["pump_index"].isin(set(universe["pump_index"]))]
    return frame.reset_index(drop=True), matrix_path


def fit_predict(x_tr, y_tr, x_te) -> np.ndarray:
    model = RandomForestClassifier(**RF_PARAMS, n_jobs=-1)
    model.fit(x_tr, y_tr)
    return model.predict_proba(x_te)[:, 1]


def run_s0(frame: pd.DataFrame) -> tuple[dict, np.ndarray]:
    x = frame[FEATURES].to_numpy(dtype=np.float64)
    y = frame["gt"].to_numpy(dtype=int)
    oof = np.full(len(y), np.nan)
    fold_ap = []
    splitter = StratifiedKFold(n_splits=OUTER_FOLDS, shuffle=False)
    for train_idx, test_idx in splitter.split(x, y):
        scores = fit_predict(x[train_idx], y[train_idx], x[test_idx])
        oof[test_idx] = scores
        fold_ap.append(float(average_precision_score(y[test_idx], scores)))
    assert not np.isnan(oof).any()
    metrics = {
        "family": "S0_ROW_5FOLD",
        "n_rows": int(len(y)),
        "prevalence": float(y.mean()),
        "pooled_oof_average_precision": float(average_precision_score(y, oof)),
        "pooled_oof_roc_auc": float(roc_auc_score(y, oof)),
        "per_fold_average_precision": fold_ap,
        "at_tau_anchor": binary_metrics(y, oof >= EM.REPLICATION_ANCHOR_TAU),
        "event_level": "not reported: rows of one event appear in both train and test",
    }
    return metrics, oof


def run_s1(frame: pd.DataFrame, bin_seconds: int) -> tuple[dict, np.ndarray, pd.DataFrame]:
    x = frame[FEATURES].to_numpy(dtype=np.float64)
    y = frame["gt"].to_numpy(dtype=int)
    groups = frame["pump_index"].to_numpy()
    oof = np.full(len(y), np.nan)
    fold_records = []
    outcomes_anchor: list = []
    outcomes_tau_star: list = []
    fold_assignment = {}

    splitter = GroupKFold(n_splits=OUTER_FOLDS)
    for fold, (train_idx, test_idx) in enumerate(splitter.split(x, y, groups)):
        # tau*_fold from event-grouped inner OOF on the outer-train only.
        inner_oof = np.full(len(train_idx), np.nan)
        inner_splitter = GroupKFold(n_splits=INNER_FOLDS)
        for in_tr, in_te in inner_splitter.split(
            x[train_idx], y[train_idx], groups[train_idx]
        ):
            inner_oof[in_te] = fit_predict(
                x[train_idx][in_tr], y[train_idx][in_tr], x[train_idx][in_te]
            )
        assert not np.isnan(inner_oof).any()
        inner_y = y[train_idx]
        if inner_y.sum() == 0:
            tau_star, fallback = EM.REPLICATION_ANCHOR_TAU, True
        else:
            tau_star, _ = EM.select_tau_star(inner_y, inner_oof)
            fallback = False

        scores = fit_predict(x[train_idx], y[train_idx], x[test_idx])
        oof[test_idx] = scores

        test_frame = frame.iloc[test_idx]
        score_series = pd.Series(scores, index=test_frame.index)
        classification = EM.classify_events(test_frame)
        for event_id in classification.eligible:
            group_rows = test_frame.loc[test_frame["pump_index"] == event_id]
            group_scores = score_series.loc[group_rows.index].to_numpy()
            outcomes_anchor.append(
                EM.score_event(group_rows, group_scores, EM.REPLICATION_ANCHOR_TAU, bin_seconds)
            )
            outcomes_tau_star.append(
                EM.score_event(group_rows, group_scores, tau_star, bin_seconds)
            )
        for event_id in np.unique(groups[test_idx]):
            fold_assignment[int(event_id)] = fold
        fold_records.append(
            {
                "fold": fold,
                "tau_star_fold": float(tau_star),
                "tau_star_fallback": fallback,
                "fold_average_precision": float(
                    average_precision_score(y[test_idx], scores)
                ),
                "n_test_events": int(len(np.unique(groups[test_idx]))),
                "n_eligible_test_events": len(classification.eligible),
            }
        )

    assert not np.isnan(oof).any()

    def pooled_summary(outcomes):
        summary = EM.summarize_events(outcomes)
        exact = np.array([float(o.exact_hit) for o in outcomes])
        hit120 = np.array([float(o.detection_hits[120]) for o in outcomes])
        episodes = np.array(summary.benchmark_negative_episodes_by_event, dtype=float)
        return {
            "n_eligible_events": summary.n_eligible,
            "edr_exact": summary.edr_exact,
            "edr_exact_ci95": EM.cluster_bootstrap_interval(exact, BOOT_N, BOOT_SEED),
            "edr_at": {str(h): v for h, v in summary.edr_at.items()},
            "edr_at_120_ci95": EM.cluster_bootstrap_interval(hit120, BOOT_N, BOOT_SEED),
            "lead_at": {str(h): v for h, v in summary.lead_at.items()},
            "delay_median_s": summary.delay_median,
            "delay_q25_s": summary.delay_q25,
            "delay_q75_s": summary.delay_q75,
            "delay_p90_s": summary.delay_p90,
            "n_detected_within_120s": summary.n_detected_within_delay_horizon,
            "benchmark_negative_mean": summary.benchmark_negative_mean,
            "benchmark_negative_mean_ci95": EM.cluster_bootstrap_interval(
                episodes, BOOT_N, BOOT_SEED
            ),
        }

    metrics = {
        "family": "S1_EVENT_5FOLD",
        "n_rows": int(len(y)),
        "prevalence": float(y.mean()),
        "pooled_oof_average_precision": float(average_precision_score(y, oof)),
        "pooled_oof_roc_auc": float(roc_auc_score(y, oof)),
        "folds": fold_records,
        "at_tau_anchor_rowlevel": binary_metrics(y, oof >= EM.REPLICATION_ANCHOR_TAU),
        "event_level_at_tau_anchor": pooled_summary(outcomes_anchor),
        "event_level_at_tau_star_fold": pooled_summary(outcomes_tau_star),
    }
    manifest = pd.DataFrame(
        sorted(fold_assignment.items()), columns=["pump_index", "fold"]
    )
    return metrics, oof, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, default=DEFAULT_UPSTREAM)
    parser.add_argument("--frequencies", nargs="*", default=list(FREQUENCIES))
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()

    args.output_root.mkdir(parents=True, exist_ok=False)
    config = {
        "spec": "protocol/formal_cv_and_ablation_spec_v0.1.md",
        "protocol_freeze_commit": PROTOCOL_FREEZE_COMMIT,
        "rf_params": RF_PARAMS,
        "features": FEATURES,
        "outer_folds": OUTER_FOLDS,
        "inner_folds": INNER_FOLDS,
        "universe": "326 common events (v3 canonical_common_event_manifest)",
        "bootstrap": {"n_boot": BOOT_N, "seed": BOOT_SEED, "cluster": "pump_index"},
        "python": platform.python_version(),
        "platform": platform.platform(),
    }
    with (args.output_root / "run_config.json").open("w") as handle:
        json.dump(config, handle, indent=2)

    for frequency in args.frequencies:
        print(f"[cv] {frequency}", flush=True)
        frame, matrix_path = load_universe(frequency, args.upstream)
        bin_seconds = EM.FREQUENCY_BIN_SECONDS[frequency]
        out_dir = args.output_root / frequency
        out_dir.mkdir(parents=True, exist_ok=False)

        s0_metrics, s0_oof = run_s0(frame)
        print(
            f"  S0 pooled AP={s0_metrics['pooled_oof_average_precision']:.4f}",
            flush=True,
        )
        s1_metrics, s1_oof, s1_manifest = run_s1(frame, bin_seconds)
        print(
            f"  S1 pooled AP={s1_metrics['pooled_oof_average_precision']:.4f} "
            f"EDR@120(anchor)={s1_metrics['event_level_at_tau_anchor']['edr_at']['120']:.3f}",
            flush=True,
        )

        with (out_dir / "metrics.json").open("w") as handle:
            json.dump({"S0": s0_metrics, "S1": s1_metrics}, handle, indent=2)
        s1_manifest.to_csv(out_dir / "s1_fold_manifest.csv", index=False)
        predictions = frame[["pump_index", "date", "gt"]].assign(
            s0_oof=s0_oof, s1_oof=s1_oof
        )
        with gzip.open(out_dir / f"predictions_{frequency}_cv.csv.gz", "wt") as handle:
            predictions.to_csv(handle, index=False)
        with (out_dir / "input_manifest.json").open("w") as handle:
            json.dump(
                {
                    "matrix": f"upstream:labeled_features/{matrix_path.name}",
                    "matrix_sha256": sha256(matrix_path),
                    "universe_manifest": "artifacts/gate0_common_calendar_forward_v3_20260721/canonical_common_event_manifest.csv",
                },
                handle,
                indent=2,
            )
    print("[done]", flush=True)


if __name__ == "__main__":
    main()
