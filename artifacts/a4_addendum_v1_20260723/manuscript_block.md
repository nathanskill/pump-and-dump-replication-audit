# A4 addendum — ready-to-paste manuscript tables

Source: `protocol/amendment_A4_analysis_addendum.md` (spec commit 78c6b45); runner `src/run_a4_addendum.py`; event-cluster bootstrap (whole events by `pump_index`, multiplicity draws), n = 2000, seed = 20260722, percentile 95% CIs. Benchmark-faithful quantities only.

## Table A4-1 — AP with event-cluster bootstrap 95% CIs (A4.1) and paired ΔAP under a shared event resample (A4.2)

| Frequency | S0 pooled OOF AP [95% CI] | S1 pooled OOF AP [95% CI] | S2 primary (80%) AP [95% CI] | ΔAP (S1 − S0) [95% CI] |
|---|---|---|---|---|
| 25S | 0.9649 [0.9485, 0.9789] | 0.9636 [0.9468, 0.9777] | 0.9781 [0.9481, 0.9992] | -0.0013 [-0.0039, 0.0009] |
| 15S | 0.9462 [0.9254, 0.9650] | 0.9466 [0.9249, 0.9658] | 0.9572 [0.9171, 0.9907] | +0.0004 [-0.0022, 0.0030] |
| 5S | 0.9025 [0.8756, 0.9287] | 0.9007 [0.8733, 0.9272] | 0.9072 [0.8453, 0.9569] | -0.0017 [-0.0051, 0.0012] |

S0/S1: pooled out-of-fold predictions over the 326-event common universe; S2: primary common-calendar forward checkpoint (80%), 66 held-out test events. The ΔAP interval is paired: the identical event resample is applied to both families. Descriptive only; a ΔAP CI covering zero supports family-insensitivity, nothing more.

## Table A4-2 — matched-universe comparison on the S2 primary test events (A4.3)

| Frequency | n test events | S1 pooled OOF AP on S2 test events [95% CI] | S2 primary AP [95% CI] |
|---|---|---|---|
| 25S | 66 | 0.9785 [0.9489, 0.9986] | 0.9781 [0.9481, 0.9992] |
| 15S | 66 | 0.9591 [0.9191, 0.9898] | 0.9572 [0.9171, 0.9907] |
| 5S | 66 | 0.9148 [0.8593, 0.9629] | 0.9072 [0.8453, 0.9569] |

Both columns score the identical 66-event test universe; S1 scores are cross-validation out-of-fold predictions, S2 scores come from the single forward-trained model.

## Table A4-3 — protocol-mandated event-level outcomes, extracted from the frozen artifacts (A4.4)

EDR@30 = EDR@60 = EDR@120 does hold in every family × frequency × threshold cell below, so a single EDR@30/60/120 column is shown.

| Family | Freq | Threshold | EDR@30/60/120 | Lead@30 | Lead@60 | Lead@120 | Delay median [IQR] (s) | Delay p90 (s) | n_det/n_elig | Bench-neg mean [95% CI] | Bench-neg median |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | 25S | τ = 0.5 (anchor) | 0.886 | 0.003 | 0.003 | 0.003 | 25.0 [25.0, 25.0] | 25.0 | 281/317 | 0.03 [0.01, 0.05] | n/p† |
| S1 | 25S | τ\*_fold (0.527, 0.500, 0.502, 0.499, 0.442) | 0.880 | 0.003 | 0.003 | 0.003 | 25.0 [25.0, 25.0] | 25.0 | 279/317 | 0.03 [0.01, 0.05] | n/p† |
| S2 | 25S | τ = 0.5 (anchor) | 0.922 | 0.000 | 0.000 | 0.000 | 25.0 [25.0, 25.0] | 25.0 | 59/64 | 0.00 [0.00, 0.00] | 0.0 |
| S2 | 25S | τ\* = 0.7037 | 0.875 | 0.000 | 0.000 | 0.000 | 25.0 [25.0, 25.0] | 25.0 | 56/64 | 0.00 [0.00, 0.00] | 0.0 |
| S1 | 15S | τ = 0.5 (anchor) | 0.845 | 0.009 | 0.013 | 0.013 | 15.0 [15.0, 15.0] | 15.0 | 268/317 | 0.03 [0.01, 0.05] | n/p† |
| S1 | 15S | τ\*_fold (0.488, 0.482, 0.389, 0.517, 0.479) | 0.842 | 0.013 | 0.016 | 0.016 | 15.0 [15.0, 15.0] | 15.0 | 267/317 | 0.03 [0.02, 0.06] | n/p† |
| S2 | 15S | τ = 0.5 (anchor) | 0.859 | 0.016 | 0.031 | 0.031 | 15.0 [15.0, 15.0] | 15.0 | 55/64 | 0.03 [0.00, 0.08] | 0.0 |
| S2 | 15S | τ\* = 0.5059 | 0.859 | 0.016 | 0.031 | 0.031 | 15.0 [15.0, 15.0] | 15.0 | 55/64 | 0.03 [0.00, 0.08] | 0.0 |
| S1 | 5S | τ = 0.5 (anchor) | 0.710 | 0.019 | 0.022 | 0.022 | 5.0 [5.0, 5.0] | 5.0 | 225/317 | 0.03 [0.01, 0.05] | n/p† |
| S1 | 5S | τ\*_fold (0.390, 0.355, 0.372, 0.387, 0.352) | 0.732 | 0.047 | 0.050 | 0.054 | 5.0 [5.0, 5.0] | 5.0 | 232/317 | 0.08 [0.05, 0.12] | n/p† |
| S2 | 5S | τ = 0.5 (anchor) | 0.641 | 0.094 | 0.109 | 0.109 | 5.0 [5.0, 5.0] | 5.0 | 41/64 | 0.11 [0.05, 0.19] | 0.0 |
| S2 | 5S | τ\* = 0.3382 | 0.734 | 0.109 | 0.125 | 0.125 | 5.0 [5.0, 5.0] | 5.0 | 47/64 | 0.14 [0.06, 0.23] | 0.0 |

† benchmark-negative medians were not persisted in the CV (S1) artifacts; per A4.4 nothing is recomputed, so only the persisted mean and its cluster CI are reported there. Delay statistics are conditional on detection within 120 s and reported with their denominators (n_det/n_elig). S1 τ\*_fold values are the five per-fold inner-selected thresholds; event outcomes are pooled across folds at each fold's own τ\*. Lead@L counts emitted alerts with availability in [t0 − L, t0]; benchmark-negative episodes are emitted alerts sourced from gt = 0 rows under the 30-minute cooldown. All quantities are benchmark-faithful on the event-centred public matrices; no real-market claims.
