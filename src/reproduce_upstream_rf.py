#!/usr/bin/env python3
"""New implementation of the published RF evaluation for REF-2026-016.

This script reproduces the upstream row-stratified five-fold experiment while
adding probabilities, fold manifests, environment metadata, and file hashes.
It does not import or execute the upstream classifier module.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold


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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_empty(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise SystemExit(f"Refusing non-empty output directory: {path}")
    path.mkdir(parents=True, exist_ok=True)


def run_frequency(
    input_path: Path,
    output_root: Path,
    frequency: str,
    *,
    n_estimators: int,
    max_depth: int,
    min_samples_leaf: int,
    random_state: int,
) -> dict:
    print(f"[{utc_now()}] loading {frequency}", flush=True)
    frame = pd.read_csv(input_path, usecols=FEATURES + ["gt"])
    x = frame[FEATURES].to_numpy(dtype=np.float64, copy=False)
    y = frame["gt"].to_numpy(dtype=np.int8, copy=False)
    splitter = StratifiedKFold(n_splits=5, shuffle=False)
    prediction = np.empty(len(frame), dtype=np.int8)
    probability = np.empty(len(frame), dtype=np.float64)
    fold_id = np.empty(len(frame), dtype=np.int8)
    fold_records: list[dict] = []

    for fold, (train_index, test_index) in enumerate(splitter.split(x, y)):
        print(
            f"[{utc_now()}] {frequency} fold={fold} "
            f"train={len(train_index)} test={len(test_index)}",
            flush=True,
        )
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_leaf=min_samples_leaf,
            random_state=random_state,
            n_jobs=-1,
        )
        model.fit(x[train_index], y[train_index])
        prediction[test_index] = model.predict(x[test_index]).astype(np.int8)
        probability[test_index] = model.predict_proba(x[test_index])[:, 1]
        fold_id[test_index] = fold
        fold_records.append(
            {
                "frequency": frequency,
                "fold": fold,
                "n_train": int(len(train_index)),
                "n_test": int(len(test_index)),
                "positive_train": int(y[train_index].sum()),
                "positive_test": int(y[test_index].sum()),
            }
        )

    metrics = {
        "frequency": frequency,
        "rows": int(len(y)),
        "positives": int(y.sum()),
        "precision": float(precision_score(y, prediction, zero_division=0)),
        "recall": float(recall_score(y, prediction, zero_division=0)),
        "f1": float(f1_score(y, prediction, zero_division=0)),
        "average_precision": float(average_precision_score(y, probability)),
        "roc_auc": float(roc_auc_score(y, probability)),
        "n_estimators": n_estimators,
        "max_depth": max_depth,
        "min_samples_leaf": min_samples_leaf,
        "random_state": random_state,
        "folds": 5,
        "shuffle": False,
    }
    predictions = pd.DataFrame(
        {
            "source_row": np.arange(len(y), dtype=np.int64),
            "fold": fold_id,
            "gt": y,
            "prediction": prediction,
            "probability": probability,
        }
    )
    prediction_path = output_root / f"predictions_{frequency}.csv.gz"
    predictions.to_csv(prediction_path, index=False, compression="gzip")
    pd.DataFrame(fold_records).to_csv(
        output_root / f"fold_manifest_{frequency}.csv", index=False
    )
    metrics["prediction_sha256"] = sha256(prediction_path)
    print(f"[{utc_now()}] completed {frequency}: {json.dumps(metrics)}", flush=True)
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--frequencies", nargs="+", default=["25S", "15S", "5S"])
    parser.add_argument("--n-estimators", type=int, default=200)
    parser.add_argument("--max-depth", type=int, default=5)
    parser.add_argument("--min-samples-leaf", type=int, default=1)
    parser.add_argument("--random-state", type=int, default=1)
    args = parser.parse_args()

    output_root = args.output_root.resolve()
    ensure_empty(output_root)
    started = utc_now()
    metrics: list[dict] = []
    inputs: list[dict] = []
    for frequency in args.frequencies:
        input_path = args.data_root.resolve() / f"features_{frequency}.csv.gz"
        if not input_path.exists():
            raise FileNotFoundError(input_path)
        inputs.append(
            {
                "frequency": frequency,
                "filename": input_path.name,
                "bytes": input_path.stat().st_size,
                "sha256": sha256(input_path),
            }
        )
        metrics.append(
            run_frequency(
                input_path,
                output_root,
                frequency,
                n_estimators=args.n_estimators,
                max_depth=args.max_depth,
                min_samples_leaf=args.min_samples_leaf,
                random_state=args.random_state,
            )
        )

    pd.DataFrame(metrics).to_csv(output_root / "metrics.csv", index=False)
    pd.DataFrame(inputs).to_csv(output_root / "input_manifest.csv", index=False)
    environment = {
        "started_at_utc": started,
        "finished_at_utc": utc_now(),
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "script_sha256": sha256(Path(__file__).resolve()),
        "features": FEATURES,
        "model": {
            "class": "RandomForestClassifier",
            "n_estimators": args.n_estimators,
            "max_depth": args.max_depth,
            "min_samples_leaf": args.min_samples_leaf,
            "random_state": args.random_state,
            "n_jobs": -1,
        },
        "evaluation": {
            "class": "StratifiedKFold",
            "n_splits": 5,
            "shuffle": False,
        },
    }
    (output_root / "environment.json").write_text(
        json.dumps(environment, indent=2), encoding="utf-8"
    )
    manifest_rows = []
    for path in sorted(output_root.iterdir()):
        if path.is_file():
            manifest_rows.append(
                {"filename": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
            )
    pd.DataFrame(manifest_rows).to_csv(output_root / "artifact_manifest.csv", index=False)
    print(f"[{utc_now()}] all requested frequencies complete", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
