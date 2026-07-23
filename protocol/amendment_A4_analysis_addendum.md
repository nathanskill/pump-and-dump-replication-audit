# Amendment A4 — analysis addendum: uncertainty and matched-universe comparisons (spec before execution)

Date: 2026-07-23 (Australia/Sydney). Status: SPEC — committed before any A4 computation is run.

## Scope and discipline

This addendum adds *reporting* mandated by internal red-team review. It introduces no new models, no re-tuning, no new thresholds, and no new claims. All computations run on the existing frozen prediction outputs of the formal runs (or, where per-row predictions were not persisted, on deterministic regeneration with the frozen configurations and `random_state=1`, verified to reproduce the archived aggregate metrics before use). Bootstrap convention follows the frozen protocol: resample whole events with replacement, n = 2000, seed = 20260722, percentile 95% intervals.

## A4.1 AP uncertainty

Event-cluster bootstrap CIs for: S0 pooled OOF AP, S1 pooled OOF AP (per frequency), and S2 primary-checkpoint AP (per frequency). Rows of a resampled event enter with multiplicity equal to the event's draw count.

## A4.2 Paired ΔAP

ΔAP(S1 − S0) per frequency under a *shared* event resample (the same bootstrap draw applied to both families), yielding a 95% CI on the difference. Interpretation boundary: descriptive; a CI covering zero supports family-insensitivity, nothing more.

## A4.3 Matched-universe comparison

S1 pooled OOF predictions restricted to exactly the S2 primary-checkpoint test events; AP per frequency on that subset, with cluster-bootstrap CI, reported next to the S2 primary AP. Purpose: an apples-to-apples family comparison on an identical test universe.

## A4.4 Protocol-mandated outcome extraction

From existing artifacts only (no recomputation): per family × frequency at the anchor threshold and τ* — EDR@30/60/120 (with the observed @30=@60=@120 equality stated explicitly if it holds), Lead@30/60/120, delay median/IQR/p90 with n_detected/n_eligible denominators, and benchmark-negative episodes mean/median with 95% cluster CI. Output as one compact table for the manuscript.

## Outputs

`artifacts/a4_addendum_v1_<UTCdate>/` containing the runner script reference, `summary.json`/`summary.csv`, and a rendered markdown block; hashes in an artifact manifest. The manuscript may then cite these values; wording changes remain governed by A1/A2 claim boundaries.
