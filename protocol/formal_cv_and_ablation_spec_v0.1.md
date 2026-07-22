# Formal S1/S0 Comparison Runs and Time-Feature Ablation — Spec v0.1

> Date: 2026-07-22. Frozen before execution; commits after this file may run
> these designs. Complements the frozen protocol v0.2 (`23089ce`) and
> amendment A1 (`d52f8ae`). No change to any frozen outcome definition.

## Shared universe

All three evaluation families are compared on the **same row universe**: rows
belonging to the 326 common events of the v3 partition design. This keeps
family differences attributable to the split logic, not to universe
composition. The Gate 0 full-universe released-code rerun remains archived
separately as the replication anchor.

## S1_EVENT_5FOLD (formal)

- Event-exclusive `GroupKFold(5)` by `pump_index`, events ordered by sorted
  `pump_index` (deterministic);
- per outer fold: released-code RF trained on the other four folds;
- `tau*_fold`: event-grouped inner `GroupKFold(4)` on the outer-training
  events produces out-of-fold probabilities; `select_tau_star` (chunk-level
  F1, ties to the higher threshold) picks the fold's threshold; the declared
  fallback (no inner positives -> 0.5) applies;
- row level: pooled out-of-fold AP over all rows (every row scored by the
  model that never saw its event), plus per-fold AP;
- event level: each eligible event is held out exactly once; outcomes are
  computed under its fold's model at `tau=0.5` and at that fold's
  `tau*_fold`, then pooled over all eligible events; cluster bootstrap as in
  the frozen spec.

## S0_ROW_5FOLD (comparable variant)

- Upstream-style non-shuffled stratified row-level 5-fold on the same
  universe, rows in file order; released-code RF; pooled out-of-fold scores;
- reports chunk-level metrics only (AP, ROC-AUC, P/R/F1 at `tau=0.5`), per
  the frozen protocol: no event-level detection or delay, because rows of one
  event appear on both sides of the split;
- no `tau*` for S0: it exists to represent the upstream evaluation family,
  anchored at the released `predict()` behaviour.

## Time-feature ablation (S2 only)

- Question: how much of the forward-time result depends on the four cyclical
  time-of-day columns (`hour_sin`, `hour_cos`, `minute_sin`, `minute_cos`)?
  The matrices are event-centred windows, so time-of-day may act as a
  position proxy rather than market signal.
- Design: rerun the S2 pipeline identically with the 8 remaining features;
  all 15 frequency x checkpoint combinations; `tau*` is re-selected on the
  ablated model's own inner validation (never copied from the full model);
- report side-by-side AP and event-level deltas. Wording boundary: results
  are a descriptive sensitivity; a drop does NOT prove leakage and a null
  effect does NOT prove its absence. No checkpoint or frequency is dropped.

## Outputs

Non-overwriting artifact directories `formal_s1_s0_v1_20260722/` and
`formal_forward_ablation_v1_20260722/` with config, input hashes, per-run
metrics, fold manifests and pooled predictions (predictions stay local).
