# REF-2026-016 Gate 0 Checklist v0.1

> Status: `OPEN / REDESIGN / CONDITIONAL GO`  
> Deadline: Day 10 after production start  
> Allowed verdicts: `GO / REDESIGN / STOP`

| Gate | Required artifact | Current state | Pass evidence |
|---|---|---|---|
| Data/code licence | source and redistribution audit | Partial | root MIT and hashes recorded; code use boundary clear; data-file redistribution remains conservatively disabled pending clarification |
| Baseline traceability | released code and paper-described RF, non-shuffled row-level stratified 5-fold | Partial pass | captured upstream stdout and the newly written implementation have matching aggregate P/R/F1 at all three frequencies; AP is new-implementation-only; paper Table III remains unresolved because article parameters, released code and post-paper matrices differ; E-103 |
| Prior replication | citation-forward matrix and ReScience fit | Initial documented screen complete / scope query pending | E-107 found a partial RF baseline reimplementation and a same-lineage chronological extension, but no study in the recorded screen that both reimplements the released RF baseline on the 5/15/25-second matrices and evaluates event-exclusive plus forward-time holdouts. Do not claim `first` or `no prior replication`; article type remains `Replication / candidate partial replication` and editor scope remains pending |
| Forward checkpoints | one primary plus at least four sensitivity checkpoints with outcome-label-free (`gt`-free), purged, event-exclusive assignment | Partial pass after redesign | identical common-calendar cutoffs and the 326-event intersection are used across 25S/15S/5S; 80% is primary and 40/50/60/70% are dependent sensitivity checkpoints; all five must be retained and reported separately; positive-event counts were inspected in the Gate 0 pilot |
| Invariants | no train/test row/event overlap; strict train-before-test; no `gt` in split assignment | Partial pass | 15 redesigned partitions and three unit tests pass; row-baseline full-run manifests exist, but event/forward model-run manifests remain pending |
| Label provenance | public outcome labels can be traced and characterised | Pending | upstream README describes manual pump-start labelling, but public feature code initializes `gt=0`; the manual label-generation step is not public and 10 event groups have no positive label |
| Event metrics | zero point, lead/lag window, alert aggregation and threshold rule frozen before model runs | Candidate specification complete / tests pending | E-106 fixes the benchmark onset-bin reference, `tau=0.5` replication anchor, training-only calibrated sensitivity, 30-minute cooldown, strict hit, 30/60/120-second post-onset and lead windows, delay and benchmark-negative episodes. Protocol v0.2 plus unit tests remain required before outer model runs |
| Feature ablation | time-only, no-time, rush-order-only | Pending | frozen configs and results plan |
| Construct boundary | event-centred ±24h corpus is not natural market flow | Verified | upstream feature script; median group span ≈47.9h; E-100 and structural audit |
| Nathan comprehension | six concepts explained in Nathan's words | Pending | dated notes or recorded mock explanation |

## Six concepts Nathan must explain

1. Why non-shuffled row-level stratified CV with event/time mixing, event-exclusive CV, and time-forward tests answer different questions;
2. Why `pump_index` and time may define a split but `gt` must not;
3. Why AP is more informative than accuracy under extreme class imbalance;
4. The difference between a model risk score and a model-level test result;
5. Why this event-centred corpus cannot estimate real deployment prevalence or daily false alerts;
6. Why a small difference or null result can still be a valid reproducibility finding.

## Stop rule

Do not compensate for a failed Gate 0 by adding more algorithms. If the released-code baseline, valid forward checkpoints, label provenance sufficient for the intended claims, or split invariants cannot be established, record the failure and redesign or downgrade the work to a technical report. If the paper-era artifact remains unavailable, proceed only as an explicitly partial replication/artifact audit after confirming venue fit; documented non-availability does not upgrade the work to an exact replication.
