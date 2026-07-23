#!/usr/bin/env python3
"""Amendment A4 — analysis addendum: uncertainty and matched-universe comparisons.

Spec: protocol/amendment_A4_analysis_addendum.md (committed at 78c6b45 before
any A4 computation was run). This runner adds *reporting only*: no new models,
no re-tuning, no new thresholds, no new claims.

Inputs (all frozen, none modified):
- artifacts/formal_s1_s0_v1_20260722/{25S,15S,5S}/predictions_<f>_cv.csv.gz
  (per-row pooled OOF predictions: columns pump_index, date, gt, s0_oof, s1_oof)
  and metrics.json (archived aggregates, A4.4 extraction source for S1);
- artifacts/formal_forward_v1_20260722/{25S,15S,5S}_80/predictions_<f>_80.csv.gz
  (per-row S2 primary-checkpoint test predictions: pump_index, date, gt, score)
  and metrics.json (archived aggregates, A4.4 extraction source for S2);
- artifacts/gate0_common_calendar_forward_v3_20260721/event_partition_80.csv
  (referenced by the forward runs' input_manifest.json; source of the S2
  primary test-event ids for A4.3, cross-checked against the events actually
  present in the forward prediction files).

Because per-row predictions were persisted by the formal runs, no deterministic
regeneration is required. Before any bootstrap, this runner re-computes each
pooled/primary AP from the persisted predictions and verifies agreement with
the archived metrics.json values to 1e-6 (abort otherwise).

Bootstrap convention (frozen protocol, mirrored from event_metrics.
cluster_bootstrap_interval): resample whole events (cluster = pump_index) with
replacement, rows of a resampled event enter with multiplicity equal to the
event's draw count; n_boot = 2000; seed = 20260722 (fresh
numpy.random.default_rng per interval family, draws of rng.integers(0, n, n)
per replicate); percentile 95% intervals (numpy linear interpolation).

- A4.1: event-cluster bootstrap CIs for S0 pooled OOF AP, S1 pooled OOF AP and
  S2 primary-checkpoint AP, per frequency.
- A4.2: paired dAP(S1 - S0) per frequency under a *shared* event resample: the
  identical draw is applied to both families' pooled OOF predictions (they
  share the 326-event universe), and the percentile CI is taken over the 2000
  per-replicate differences. Descriptive only.
- A4.3: S1 pooled OOF predictions restricted to exactly the S2 primary (80%)
  test-event set; AP with cluster-bootstrap CI, next to the S2 primary AP.
- A4.4: extraction ONLY from the existing metrics.json files (no event-metric
  recomputation): per family x frequency at the anchor threshold and tau* —
  EDR@30/60/120, Lead@30/60/120, delay median/IQR/p90 with
  n_detected/n_eligible, benchmark-negative episode mean/median with the 95%
  cluster CI where persisted (the CV artifacts persist the mean and its CI but
  not the median; this is stated, not recomputed).

Weighted-AP implementation note: multiplicity-weighted AP is computed by a
fast presorted cumulative-sum routine (AP = sum_k (R_k - R_{k-1}) P_k over
distinct-score groups in decreasing-score order — sklearn's definition). It is
validated at runtime against sklearn.metrics.average_precision_score both on
the full data (all multiplicities 1) and, for the first two bootstrap
replicates of every interval, against explicit row duplication via np.repeat
(tolerance 1e-9; abort on failure).

Outputs (non-overwriting) in artifacts/a4_addendum_v1_20260723/:
summary.json, summary.csv, manuscript_block.md, artifact_manifest.csv.

Benchmark-faithful quantities only; no real-market claims. Wording remains
governed by the A1/A2 claim boundaries.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import average_precision_score

ROOT = Path(__file__).resolve().parents[1]

A4_SPEC = "protocol/amendment_A4_analysis_addendum.md"
A4_SPEC_COMMIT = "78c6b45"
PROTOCOL_FREEZE_COMMIT = "c2736ed36e6a074ded78e916c071d5d396b316c3"

FREQUENCIES = ("25S", "15S", "5S")
BOOT_N = 2000
BOOT_SEED = 20260722
ALPHA = 0.05
AP_VERIFY_TOL = 1e-6
FAST_AP_TOL = 1e-9

CV_ROOT = ROOT / "artifacts" / "formal_s1_s0_v1_20260722"
FWD_ROOT = ROOT / "artifacts" / "formal_forward_v1_20260722"
PARTITION_80 = (
    ROOT
    / "artifacts"
    / "gate0_common_calendar_forward_v3_20260721"
    / "event_partition_80.csv"
)
OUTPUT_ROOT = ROOT / "artifacts" / "a4_addendum_v1_20260723"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class WeightedAP:
    """Multiplicity-weighted average precision on a fixed row universe.

    Rows are presorted once by decreasing score (stable mergesort); each call
    evaluates AP with per-event integer multiplicities in O(n) via cumulative
    sums over distinct-score groups. Identical to duplicating every row of an
    event `count` times and calling sklearn's average_precision_score
    (validated at runtime).
    """

    def __init__(self, scores: np.ndarray, y: np.ndarray, event_codes: np.ndarray):
        order = np.argsort(-scores, kind="mergesort")
        self.scores = scores[order]
        self.y = y[order].astype(np.float64)
        self.codes = event_codes[order]
        boundaries = np.nonzero(np.diff(self.scores))[0]
        self.group_ends = np.append(boundaries, len(self.scores) - 1)

    def ap(self, event_multiplicity: np.ndarray) -> float:
        w = event_multiplicity[self.codes].astype(np.float64)
        tps = np.cumsum(w * self.y)[self.group_ends]
        ps = np.cumsum(w)[self.group_ends]
        total_pos = tps[-1]
        if total_pos <= 0:
            raise ValueError("bootstrap replicate contains no positive rows")
        precision = np.divide(tps, ps, out=np.zeros_like(tps), where=ps > 0)
        recall = tps / total_pos
        return float(np.sum(np.diff(recall, prepend=0.0) * precision))


def event_codes(pump_index: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Sorted unique event ids and the per-row integer code into them."""
    events = np.unique(pump_index)
    return events, np.searchsorted(events, pump_index)


def bootstrap_counts(n_events: int, n_boot: int = BOOT_N, seed: int = BOOT_SEED) -> np.ndarray:
    """Deterministic (n_boot, n_events) multiplicity matrix.

    Mirrors event_metrics.cluster_bootstrap_interval's draw convention: a
    fresh default_rng(seed), one rng.integers(0, n, size=n) draw per
    replicate, in replicate order.
    """
    rng = np.random.default_rng(seed)
    counts = np.empty((n_boot, n_events), dtype=np.int64)
    for b in range(n_boot):
        counts[b] = np.bincount(rng.integers(0, n_events, size=n_events), minlength=n_events)
    return counts


def percentile_ci(values: np.ndarray, alpha: float = ALPHA) -> tuple[float, float]:
    lower = float(np.percentile(values, 100 * (alpha / 2)))
    upper = float(np.percentile(values, 100 * (1 - alpha / 2)))
    return lower, upper


def sklearn_ap_by_duplication(
    y: np.ndarray, scores: np.ndarray, row_multiplicity: np.ndarray
) -> float:
    """Reference AP with rows explicitly duplicated to their multiplicity."""
    idx = np.repeat(np.arange(len(y)), row_multiplicity)
    return float(average_precision_score(y[idx], scores[idx]))


def validate_fast_ap(
    ap_engine: WeightedAP,
    y: np.ndarray,
    scores: np.ndarray,
    codes: np.ndarray,
    counts: np.ndarray,
    label: str,
) -> dict:
    """Runtime validation of the fast weighted AP against sklearn."""
    ones = np.ones(counts.shape[1], dtype=np.int64)
    full_fast = ap_engine.ap(ones)
    full_sklearn = float(average_precision_score(y, scores))
    checks = {"full_data_abs_diff": abs(full_fast - full_sklearn)}
    replicate_diffs = []
    for b in range(2):
        fast = ap_engine.ap(counts[b])
        ref = sklearn_ap_by_duplication(y, scores, counts[b][codes])
        replicate_diffs.append(abs(fast - ref))
    checks["replicate_abs_diffs"] = replicate_diffs
    worst = max([checks["full_data_abs_diff"]] + replicate_diffs)
    if worst > FAST_AP_TOL:
        raise AssertionError(
            f"[{label}] fast weighted AP disagrees with sklearn (max diff {worst:.3e})"
        )
    return checks


def load_cv(frequency: str) -> pd.DataFrame:
    return pd.read_csv(CV_ROOT / frequency / f"predictions_{frequency}_cv.csv.gz")


def load_fwd(frequency: str) -> pd.DataFrame:
    return pd.read_csv(FWD_ROOT / f"{frequency}_80" / f"predictions_{frequency}_80.csv.gz")


def load_json(path: Path) -> dict:
    with path.open() as handle:
        return json.load(handle)


def verify_archived_ap(recomputed: float, archived: float, label: str) -> float:
    diff = abs(recomputed - archived)
    if diff > AP_VERIFY_TOL:
        raise AssertionError(
            f"[{label}] persisted predictions do not reproduce the archived AP: "
            f"recomputed {recomputed!r} vs archived {archived!r} (diff {diff:.3e})"
        )
    return diff


def extract_event_block(block: dict, family: str) -> dict:
    """A4.4: read-only extraction of one event-level block from metrics.json."""
    n_eligible = block.get("n_eligible_events", block.get("n_eligible_test_events"))
    return {
        "n_eligible": n_eligible,
        "edr_at": {h: block["edr_at"][h] for h in ("30", "60", "120")},
        "lead_at": {h: block["lead_at"][h] for h in ("30", "60", "120")},
        "delay_median_s": block["delay_median_s"],
        "delay_q25_s": block["delay_q25_s"],
        "delay_q75_s": block["delay_q75_s"],
        "delay_p90_s": block["delay_p90_s"],
        "n_detected_within_120s": block["n_detected_within_120s"],
        "benchmark_negative_mean": block["benchmark_negative_mean"],
        "benchmark_negative_mean_ci95": block["benchmark_negative_mean_ci95"],
        "benchmark_negative_median": block.get("benchmark_negative_median"),
        "benchmark_negative_median_note": (
            None
            if "benchmark_negative_median" in block
            else f"not persisted in the {family} artifacts (mean and its CI are)"
        ),
    }


def fmt(x, nd=4) -> str:
    if x is None:
        return "—"
    return f"{x:.{nd}f}"


def fmt_ci(ci, nd=4) -> str:
    return f"[{ci[0]:.{nd}f}, {ci[1]:.{nd}f}]"


def main() -> None:
    t_start = time.time()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=False)

    # ---- S2 primary test-event ids (A4.3), read from the forward manifests.
    partition = pd.read_csv(PARTITION_80)
    s2_test_ids = np.array(
        sorted(partition.loc[partition["partition"] == "test", "pump_index"])
    )

    verification: dict = {
        "regeneration_needed": False,
        "regeneration_note": (
            "per-row predictions were persisted by the formal runs; archived "
            "aggregate APs re-verified from those files before bootstrap"
        ),
        "ap_reproduction_abs_diffs": {},
        "fast_ap_validation": {},
        "s2_test_set_checks": {},
    }
    results_a41: dict = {}
    results_a42: dict = {}
    results_a43: dict = {}
    results_a44: dict = {}
    csv_rows: list[dict] = []

    for frequency in FREQUENCIES:
        print(f"[a4] {frequency}", flush=True)
        cv = load_cv(frequency)
        fwd = load_fwd(frequency)
        cv_metrics = load_json(CV_ROOT / frequency / "metrics.json")
        fwd_metrics = load_json(FWD_ROOT / f"{frequency}_80" / "metrics.json")

        y_cv = cv["gt"].to_numpy(dtype=int)
        s0 = cv["s0_oof"].to_numpy(dtype=np.float64)
        s1 = cv["s1_oof"].to_numpy(dtype=np.float64)
        y_fwd = fwd["gt"].to_numpy(dtype=int)
        s2 = fwd["score"].to_numpy(dtype=np.float64)

        # ---- verification gate: persisted predictions must reproduce the
        # archived aggregate APs to 1e-6 before any bootstrap use.
        ap_s0 = float(average_precision_score(y_cv, s0))
        ap_s1 = float(average_precision_score(y_cv, s1))
        ap_s2 = float(average_precision_score(y_fwd, s2))
        verification["ap_reproduction_abs_diffs"][frequency] = {
            "S0_pooled_oof": verify_archived_ap(
                ap_s0, cv_metrics["S0"]["pooled_oof_average_precision"], f"{frequency} S0"
            ),
            "S1_pooled_oof": verify_archived_ap(
                ap_s1, cv_metrics["S1"]["pooled_oof_average_precision"], f"{frequency} S1"
            ),
            "S2_primary": verify_archived_ap(
                ap_s2, fwd_metrics["row_level"]["average_precision"], f"{frequency} S2"
            ),
        }

        # ---- A4.3 universe checks: partition-manifest test ids must equal the
        # events actually present in the forward predictions and be contained
        # in the CV universe.
        fwd_events = np.unique(fwd["pump_index"].to_numpy())
        cv_events_all = np.unique(cv["pump_index"].to_numpy())
        same_set = bool(np.array_equal(fwd_events, s2_test_ids))
        contained = bool(np.isin(s2_test_ids, cv_events_all).all())
        verification["s2_test_set_checks"][frequency] = {
            "partition_manifest_equals_forward_prediction_events": same_set,
            "test_ids_subset_of_cv_universe": contained,
            "n_test_events": int(len(s2_test_ids)),
        }
        if not (same_set and contained):
            raise AssertionError(f"[{frequency}] S2 test-event set mismatch")

        # ---- A4.1 + A4.2: paired cluster bootstrap on the CV universe.
        # S0 and S1 share the 326-event universe; one draw per replicate is
        # applied to both families (shared resample), so the same 2000 draws
        # yield the S0 CI, the S1 CI and the paired dAP CI.
        cv_pump = cv["pump_index"].to_numpy()
        cv_events, cv_codes = event_codes(cv_pump)
        engine_s0 = WeightedAP(s0, y_cv, cv_codes)
        engine_s1 = WeightedAP(s1, y_cv, cv_codes)
        counts_cv = bootstrap_counts(len(cv_events))
        verification["fast_ap_validation"][f"{frequency}_S0"] = validate_fast_ap(
            engine_s0, y_cv, s0, cv_codes, counts_cv, f"{frequency} S0"
        )
        verification["fast_ap_validation"][f"{frequency}_S1"] = validate_fast_ap(
            engine_s1, y_cv, s1, cv_codes, counts_cv, f"{frequency} S1"
        )
        boot_s0 = np.empty(BOOT_N)
        boot_s1 = np.empty(BOOT_N)
        for b in range(BOOT_N):
            boot_s0[b] = engine_s0.ap(counts_cv[b])
            boot_s1[b] = engine_s1.ap(counts_cv[b])
        boot_delta = boot_s1 - boot_s0

        # ---- A4.1: S2 primary AP bootstrap on its own 66-event test universe.
        fwd_pump = fwd["pump_index"].to_numpy()
        fwd_events_sorted, fwd_codes = event_codes(fwd_pump)
        engine_s2 = WeightedAP(s2, y_fwd, fwd_codes)
        counts_fwd = bootstrap_counts(len(fwd_events_sorted))
        verification["fast_ap_validation"][f"{frequency}_S2"] = validate_fast_ap(
            engine_s2, y_fwd, s2, fwd_codes, counts_fwd, f"{frequency} S2"
        )
        boot_s2 = np.array([engine_s2.ap(counts_fwd[b]) for b in range(BOOT_N)])

        # ---- A4.3: S1 pooled OOF restricted to exactly the S2 test events.
        mask = np.isin(cv_pump, s2_test_ids)
        y_r = y_cv[mask]
        s1_r = s1[mask]
        r_events, r_codes = event_codes(cv_pump[mask])
        assert np.array_equal(r_events, s2_test_ids)
        ap_s1_restricted = float(average_precision_score(y_r, s1_r))
        engine_s1r = WeightedAP(s1_r, y_r, r_codes)
        counts_r = bootstrap_counts(len(r_events))
        verification["fast_ap_validation"][f"{frequency}_S1_restricted"] = validate_fast_ap(
            engine_s1r, y_r, s1_r, r_codes, counts_r, f"{frequency} S1 restricted"
        )
        boot_s1r = np.array([engine_s1r.ap(counts_r[b]) for b in range(BOOT_N)])

        ci_s0 = percentile_ci(boot_s0)
        ci_s1 = percentile_ci(boot_s1)
        ci_s2 = percentile_ci(boot_s2)
        ci_delta = percentile_ci(boot_delta)
        ci_s1r = percentile_ci(boot_s1r)

        results_a41[frequency] = {
            "S0_pooled_oof_ap": ap_s0,
            "S0_pooled_oof_ap_ci95": ci_s0,
            "S1_pooled_oof_ap": ap_s1,
            "S1_pooled_oof_ap_ci95": ci_s1,
            "S2_primary_ap": ap_s2,
            "S2_primary_ap_ci95": ci_s2,
            "n_events_cv_universe": int(len(cv_events)),
            "n_events_s2_test": int(len(fwd_events_sorted)),
            "n_rows_cv": int(len(cv)),
            "n_rows_s2_test": int(len(fwd)),
        }
        results_a42[frequency] = {
            "delta_ap_s1_minus_s0": ap_s1 - ap_s0,
            "delta_ap_ci95": ci_delta,
            "shared_resample": True,
            "note": (
                "descriptive; a CI covering zero supports family-insensitivity, "
                "nothing more"
            ),
        }
        results_a43[frequency] = {
            "s1_oof_ap_on_s2_test_events": ap_s1_restricted,
            "s1_oof_ap_on_s2_test_events_ci95": ci_s1r,
            "s2_primary_ap": ap_s2,
            "s2_primary_ap_ci95": ci_s2,
            "n_test_events": int(len(s2_test_ids)),
            "n_rows_s1_restricted": int(mask.sum()),
            "n_rows_s2_test": int(len(fwd)),
            "row_count_note": (
                "row counts differ by design: S1 OOF rows cover each test "
                "event's full CV-universe window; the comparison is on an "
                "identical *event* universe"
            ),
        }
        print(
            f"  S0 AP={ap_s0:.4f} {fmt_ci(ci_s0)}  S1 AP={ap_s1:.4f} {fmt_ci(ci_s1)}  "
            f"S2 AP={ap_s2:.4f} {fmt_ci(ci_s2)}",
            flush=True,
        )
        print(
            f"  dAP(S1-S0)={ap_s1 - ap_s0:+.4f} {fmt_ci(ci_delta)}  "
            f"S1|S2-test AP={ap_s1_restricted:.4f} {fmt_ci(ci_s1r)}",
            flush=True,
        )

        # ---- A4.4: extraction only (no recomputation of event metrics).
        s1_folds = cv_metrics["S1"]["folds"]
        results_a44[frequency] = {
            "S1": {
                "tau_anchor": 0.5,
                "tau_star_fold_values": [f["tau_star_fold"] for f in s1_folds],
                "tau_star_fold_fallbacks": [f["tau_star_fallback"] for f in s1_folds],
                "at_tau_anchor": extract_event_block(
                    cv_metrics["S1"]["event_level_at_tau_anchor"], "CV (S1)"
                ),
                "at_tau_star": extract_event_block(
                    cv_metrics["S1"]["event_level_at_tau_star_fold"], "CV (S1)"
                ),
            },
            "S2": {
                "tau_anchor": fwd_metrics["tau_anchor"],
                "tau_star": fwd_metrics["tau_star"],
                "tau_star_fallback": fwd_metrics["tau_star_fallback_no_inner_positives"],
                "at_tau_anchor": extract_event_block(
                    fwd_metrics["event_level_at_tau_anchor"], "forward (S2)"
                ),
                "at_tau_star": extract_event_block(
                    fwd_metrics["event_level_at_tau_star"], "forward (S2)"
                ),
            },
        }

        # ---- flat CSV rows.
        for fam, metric, val, ci in (
            ("S0", "pooled_oof_ap", ap_s0, ci_s0),
            ("S1", "pooled_oof_ap", ap_s1, ci_s1),
            ("S2", "primary_ap", ap_s2, ci_s2),
        ):
            csv_rows.append(
                dict(section="A4.1", family=fam, frequency=frequency, threshold="",
                     metric=metric, value=val, ci_lo=ci[0], ci_hi=ci[1], note="")
            )
        csv_rows.append(
            dict(section="A4.2", family="S1-S0", frequency=frequency, threshold="",
                 metric="delta_pooled_oof_ap", value=ap_s1 - ap_s0,
                 ci_lo=ci_delta[0], ci_hi=ci_delta[1], note="shared event resample")
        )
        csv_rows.append(
            dict(section="A4.3", family="S1", frequency=frequency, threshold="",
                 metric="oof_ap_on_s2_test_events", value=ap_s1_restricted,
                 ci_lo=ci_s1r[0], ci_hi=ci_s1r[1],
                 note=f"restricted to the {len(s2_test_ids)} S2 primary test events")
        )
        csv_rows.append(
            dict(section="A4.3", family="S2", frequency=frequency, threshold="",
                 metric="primary_ap", value=ap_s2, ci_lo=ci_s2[0], ci_hi=ci_s2[1],
                 note="same event universe as the row above")
        )
        for fam in ("S1", "S2"):
            for thr_key, thr_label in (("at_tau_anchor", "tau=0.5"), ("at_tau_star", "tau*")):
                block = results_a44[frequency][fam][thr_key]
                if fam == "S1" and thr_key == "at_tau_star":
                    thr_label = "tau*_fold (per fold)"
                elif fam == "S2" and thr_key == "at_tau_star":
                    thr_label = f"tau*={results_a44[frequency]['S2']['tau_star']:.4f}"
                base = dict(section="A4.4", family=fam, frequency=frequency,
                            threshold=thr_label)
                for h in ("30", "60", "120"):
                    csv_rows.append({**base, "metric": f"edr_at_{h}",
                                     "value": block["edr_at"][h], "ci_lo": "", "ci_hi": "", "note": ""})
                for h in ("30", "60", "120"):
                    csv_rows.append({**base, "metric": f"lead_at_{h}",
                                     "value": block["lead_at"][h], "ci_lo": "", "ci_hi": "", "note": ""})
                for key in ("delay_median_s", "delay_q25_s", "delay_q75_s", "delay_p90_s"):
                    csv_rows.append({**base, "metric": key, "value": block[key],
                                     "ci_lo": "", "ci_hi": "", "note": ""})
                csv_rows.append({**base, "metric": "n_detected_within_120s",
                                 "value": block["n_detected_within_120s"],
                                 "ci_lo": "", "ci_hi": "",
                                 "note": f"n_eligible={block['n_eligible']}"})
                csv_rows.append({**base, "metric": "benchmark_negative_mean",
                                 "value": block["benchmark_negative_mean"],
                                 "ci_lo": block["benchmark_negative_mean_ci95"][0],
                                 "ci_hi": block["benchmark_negative_mean_ci95"][1],
                                 "note": ""})
                csv_rows.append({**base, "metric": "benchmark_negative_median",
                                 "value": block["benchmark_negative_median"],
                                 "ci_lo": "", "ci_hi": "",
                                 "note": block["benchmark_negative_median_note"] or ""})

    # ---- EDR@30/60/120 equality statement (A4.4).
    edr_equal = all(
        results_a44[f][fam][thr]["edr_at"]["30"]
        == results_a44[f][fam][thr]["edr_at"]["60"]
        == results_a44[f][fam][thr]["edr_at"]["120"]
        for f in FREQUENCIES
        for fam in ("S1", "S2")
        for thr in ("at_tau_anchor", "at_tau_star")
    )

    runtime_s = time.time() - t_start

    # ---- summary.json
    summary = {
        "amendment": "A4",
        "spec": A4_SPEC,
        "spec_commit": A4_SPEC_COMMIT,
        "protocol_freeze_commit": PROTOCOL_FREEZE_COMMIT,
        "runner": "src/run_a4_addendum.py",
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "runtime_seconds": runtime_s,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "sklearn": sklearn.__version__,
        "bootstrap": {
            "n_boot": BOOT_N,
            "seed": BOOT_SEED,
            "method": "percentile 95%",
            "cluster": "pump_index (whole events resampled with replacement; "
            "rows enter with the event's draw multiplicity)",
            "draw_convention": "fresh default_rng(seed) per interval family; "
            "rng.integers(0, n_events, size=n_events) per replicate; the CV "
            "draw is shared between S0 and S1 (paired, A4.2)",
        },
        "inputs": {
            "cv_predictions": {
                f: {
                    "path": f"artifacts/formal_s1_s0_v1_20260722/{f}/predictions_{f}_cv.csv.gz",
                    "sha256": sha256(CV_ROOT / f / f"predictions_{f}_cv.csv.gz"),
                }
                for f in FREQUENCIES
            },
            "cv_metrics": {
                f: {
                    "path": f"artifacts/formal_s1_s0_v1_20260722/{f}/metrics.json",
                    "sha256": sha256(CV_ROOT / f / "metrics.json"),
                }
                for f in FREQUENCIES
            },
            "forward_predictions": {
                f: {
                    "path": f"artifacts/formal_forward_v1_20260722/{f}_80/predictions_{f}_80.csv.gz",
                    "sha256": sha256(FWD_ROOT / f"{f}_80" / f"predictions_{f}_80.csv.gz"),
                }
                for f in FREQUENCIES
            },
            "forward_metrics": {
                f: {
                    "path": f"artifacts/formal_forward_v1_20260722/{f}_80/metrics.json",
                    "sha256": sha256(FWD_ROOT / f"{f}_80" / "metrics.json"),
                }
                for f in FREQUENCIES
            },
            "s2_test_partition": {
                "path": "artifacts/gate0_common_calendar_forward_v3_20260721/event_partition_80.csv",
                "sha256": sha256(PARTITION_80),
            },
        },
        "verification": verification,
        "A4_1_ap_uncertainty": results_a41,
        "A4_2_paired_delta_ap": results_a42,
        "A4_3_matched_universe": results_a43,
        "A4_4_outcome_extraction": {
            "edr_30_60_120_equal_everywhere": edr_equal,
            "by_frequency": results_a44,
        },
    }
    with (OUTPUT_ROOT / "summary.json").open("w") as handle:
        json.dump(summary, handle, indent=2)

    # ---- summary.csv
    pd.DataFrame(
        csv_rows,
        columns=["section", "family", "frequency", "threshold", "metric",
                 "value", "ci_lo", "ci_hi", "note"],
    ).to_csv(OUTPUT_ROOT / "summary.csv", index=False)

    # ---- manuscript_block.md
    lines: list[str] = []
    lines.append("# A4 addendum — ready-to-paste manuscript tables")
    lines.append("")
    lines.append(
        f"Source: `{A4_SPEC}` (spec commit {A4_SPEC_COMMIT}); runner "
        "`src/run_a4_addendum.py`; event-cluster bootstrap (whole events by "
        f"`pump_index`, multiplicity draws), n = {BOOT_N}, seed = {BOOT_SEED}, "
        "percentile 95% CIs. Benchmark-faithful quantities only."
    )
    lines.append("")
    lines.append("## Table A4-1 — AP with event-cluster bootstrap 95% CIs (A4.1) "
                 "and paired ΔAP under a shared event resample (A4.2)")
    lines.append("")
    lines.append("| Frequency | S0 pooled OOF AP [95% CI] | S1 pooled OOF AP [95% CI] "
                 "| S2 primary (80%) AP [95% CI] | ΔAP (S1 − S0) [95% CI] |")
    lines.append("|---|---|---|---|---|")
    for f in FREQUENCIES:
        a, d = results_a41[f], results_a42[f]
        lines.append(
            f"| {f} | {a['S0_pooled_oof_ap']:.4f} {fmt_ci(a['S0_pooled_oof_ap_ci95'])} "
            f"| {a['S1_pooled_oof_ap']:.4f} {fmt_ci(a['S1_pooled_oof_ap_ci95'])} "
            f"| {a['S2_primary_ap']:.4f} {fmt_ci(a['S2_primary_ap_ci95'])} "
            f"| {d['delta_ap_s1_minus_s0']:+.4f} {fmt_ci(d['delta_ap_ci95'])} |"
        )
    lines.append("")
    lines.append(
        "S0/S1: pooled out-of-fold predictions over the 326-event common "
        "universe; S2: primary common-calendar forward checkpoint (80%), 66 "
        "held-out test events. The ΔAP interval is paired: the identical event "
        "resample is applied to both families. Descriptive only; a ΔAP CI "
        "covering zero supports family-insensitivity, nothing more."
    )
    lines.append("")
    lines.append("## Table A4-2 — matched-universe comparison on the S2 primary "
                 "test events (A4.3)")
    lines.append("")
    lines.append("| Frequency | n test events | S1 pooled OOF AP on S2 test events "
                 "[95% CI] | S2 primary AP [95% CI] |")
    lines.append("|---|---|---|---|")
    for f in FREQUENCIES:
        r = results_a43[f]
        lines.append(
            f"| {f} | {r['n_test_events']} "
            f"| {r['s1_oof_ap_on_s2_test_events']:.4f} "
            f"{fmt_ci(r['s1_oof_ap_on_s2_test_events_ci95'])} "
            f"| {r['s2_primary_ap']:.4f} {fmt_ci(r['s2_primary_ap_ci95'])} |"
        )
    lines.append("")
    lines.append(
        "Both columns score the identical 66-event test universe; S1 scores are "
        "cross-validation out-of-fold predictions, S2 scores come from the "
        "single forward-trained model."
    )
    lines.append("")
    lines.append("## Table A4-3 — protocol-mandated event-level outcomes, "
                 "extracted from the frozen artifacts (A4.4)")
    lines.append("")
    eq_word = "does" if edr_equal else "does NOT"
    lines.append(
        f"EDR@30 = EDR@60 = EDR@120 {eq_word} hold in every family × frequency "
        "× threshold cell below, so a single EDR@30/60/120 column is shown."
        if edr_equal
        else f"EDR@30 = EDR@60 = EDR@120 {eq_word} hold everywhere; all three "
        "are shown."
    )
    lines.append("")
    if edr_equal:
        lines.append("| Family | Freq | Threshold | EDR@30/60/120 | Lead@30 | Lead@60 "
                     "| Lead@120 | Delay median [IQR] (s) | Delay p90 (s) "
                     "| n_det/n_elig | Bench-neg mean [95% CI] | Bench-neg median |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    else:
        lines.append("| Family | Freq | Threshold | EDR@30 | EDR@60 | EDR@120 | Lead@30 "
                     "| Lead@60 | Lead@120 | Delay median [IQR] (s) | Delay p90 (s) "
                     "| n_det/n_elig | Bench-neg mean [95% CI] | Bench-neg median |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for f in FREQUENCIES:
        for fam in ("S1", "S2"):
            fam_block = results_a44[f][fam]
            for thr_key in ("at_tau_anchor", "at_tau_star"):
                block = fam_block[thr_key]
                if thr_key == "at_tau_anchor":
                    thr_label = "τ = 0.5 (anchor)"
                elif fam == "S1":
                    stars = ", ".join(f"{v:.3f}" for v in fam_block["tau_star_fold_values"])
                    thr_label = f"τ\\*_fold ({stars})"
                else:
                    thr_label = f"τ\\* = {fam_block['tau_star']:.4f}"
                edr_cells = (
                    [fmt(block["edr_at"]["30"], 3)]
                    if edr_equal
                    else [fmt(block["edr_at"][h], 3) for h in ("30", "60", "120")]
                )
                if block["delay_median_s"] is None:
                    delay_cell, p90_cell = "—", "—"
                else:
                    delay_cell = (
                        f"{block['delay_median_s']:.1f} "
                        f"[{block['delay_q25_s']:.1f}, {block['delay_q75_s']:.1f}]"
                    )
                    p90_cell = f"{block['delay_p90_s']:.1f}"
                med = block["benchmark_negative_median"]
                med_cell = "n/p†" if med is None else f"{med:.1f}"
                cells = (
                    [fam, f, thr_label]
                    + edr_cells
                    + [fmt(block["lead_at"][h], 3) for h in ("30", "60", "120")]
                    + [
                        delay_cell,
                        p90_cell,
                        f"{block['n_detected_within_120s']}/{block['n_eligible']}",
                        f"{block['benchmark_negative_mean']:.2f} "
                        f"{fmt_ci(block['benchmark_negative_mean_ci95'], 2)}",
                        med_cell,
                    ]
                )
                lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    lines.append(
        "† benchmark-negative medians were not persisted in the CV (S1) "
        "artifacts; per A4.4 nothing is recomputed, so only the persisted mean "
        "and its cluster CI are reported there. Delay statistics are "
        "conditional on detection within 120 s and reported with their "
        "denominators (n_det/n_elig). S1 τ\\*_fold values are the five "
        "per-fold inner-selected thresholds; event outcomes are pooled across "
        "folds at each fold's own τ\\*. Lead@L counts emitted alerts with "
        "availability in [t0 − L, t0]; benchmark-negative episodes are emitted "
        "alerts sourced from gt = 0 rows under the 30-minute cooldown. All "
        "quantities are benchmark-faithful on the event-centred public "
        "matrices; no real-market claims."
    )
    lines.append("")
    with (OUTPUT_ROOT / "manuscript_block.md").open("w") as handle:
        handle.write("\n".join(lines))

    # ---- artifact_manifest.csv (outputs + runner + inputs; manifest excludes
    # itself).
    manifest_rows = []
    for role, rel in (
        ("output", "artifacts/a4_addendum_v1_20260723/summary.json"),
        ("output", "artifacts/a4_addendum_v1_20260723/summary.csv"),
        ("output", "artifacts/a4_addendum_v1_20260723/manuscript_block.md"),
        ("runner", "src/run_a4_addendum.py"),
        ("input", "artifacts/gate0_common_calendar_forward_v3_20260721/event_partition_80.csv"),
    ):
        manifest_rows.append({"role": role, "path": rel, "sha256": sha256(ROOT / rel)})
    for f in FREQUENCIES:
        for rel in (
            f"artifacts/formal_s1_s0_v1_20260722/{f}/predictions_{f}_cv.csv.gz",
            f"artifacts/formal_s1_s0_v1_20260722/{f}/metrics.json",
            f"artifacts/formal_forward_v1_20260722/{f}_80/predictions_{f}_80.csv.gz",
            f"artifacts/formal_forward_v1_20260722/{f}_80/metrics.json",
        ):
            manifest_rows.append({"role": "input", "path": rel, "sha256": sha256(ROOT / rel)})
    pd.DataFrame(manifest_rows).to_csv(OUTPUT_ROOT / "artifact_manifest.csv", index=False)

    print(f"[done] runtime {runtime_s:.1f}s -> {OUTPUT_ROOT}", flush=True)


if __name__ == "__main__":
    main()
