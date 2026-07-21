#!/usr/bin/env python3
"""Capture the released upstream classifier stdout and execution metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import sklearn


FREQUENCIES = ("25S", "15S", "5S")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_empty(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise SystemExit(f"Refusing non-empty output directory: {path}")
    path.mkdir(parents=True, exist_ok=True)


def parse_stdout(stdout: str) -> list[dict[str, object]]:
    pattern = re.compile(
        r"Processing: 5 folds - time freq (?P<frequency>\S+)\n"
        r"Recall: (?P<recall>[0-9.]+)\n"
        r"Precision: (?P<precision>[0-9.]+)\n"
        r"F1 score: (?P<f1>[0-9.]+)"
    )
    rows = []
    for match in pattern.finditer(stdout):
        rows.append(
            {
                "frequency": match.group("frequency"),
                "precision": float(match.group("precision")),
                "recall": float(match.group("recall")),
                "f1": float(match.group("f1")),
            }
        )
    if tuple(row["frequency"] for row in rows) != FREQUENCIES:
        raise ValueError("Could not parse all expected upstream frequency blocks")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()

    upstream_root = args.upstream_root.resolve()
    output_root = args.output_root.resolve()
    ensure_empty(output_root)
    classifier = upstream_root / "classifier.py"
    if not classifier.exists():
        raise FileNotFoundError(classifier)

    started = utc_now()
    completed = subprocess.run(
        [sys.executable, classifier.name],
        cwd=upstream_root,
        text=True,
        capture_output=True,
        check=False,
    )
    (output_root / "stdout.log").write_text(completed.stdout, encoding="utf-8")
    (output_root / "stderr.log").write_text(completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(f"Upstream classifier exited {completed.returncode}")

    pd.DataFrame(parse_stdout(completed.stdout)).to_csv(
        output_root / "metrics_from_stdout.csv", index=False
    )
    inputs = [{"filename": classifier.name, "sha256": sha256(classifier)}]
    for frequency in FREQUENCIES:
        path = upstream_root / "labeled_features" / f"features_{frequency}.csv.gz"
        inputs.append(
            {
                "filename": str(path.relative_to(upstream_root)),
                "sha256": sha256(path),
            }
        )
    pd.DataFrame(inputs).to_csv(output_root / "input_manifest.csv", index=False)

    environment = {
        "started_at_utc": started,
        "finished_at_utc": utc_now(),
        "returncode": completed.returncode,
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "capture_script_sha256": sha256(Path(__file__).resolve()),
        "upstream_classifier_sha256": sha256(classifier),
    }
    (output_root / "environment.json").write_text(
        json.dumps(environment, indent=2), encoding="utf-8"
    )
    manifest = []
    for path in sorted(output_root.iterdir()):
        if path.is_file():
            manifest.append(
                {"filename": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}
            )
    pd.DataFrame(manifest).to_csv(output_root / "artifact_manifest.csv", index=False)
    print(json.dumps(parse_stdout(completed.stdout), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
