# REF-2026-016 Manuscript Outline v0.1

## Title

A Replication Attempt and Evaluation-Sensitivity Audit of “Pump and Dumps in the Bitcoin Era”

## Abstract skeleton

1. Problem: high reported detection scores may depend on the evaluation unit and time order;
2. Gap: the public benchmark is commonly evaluated at the row level, while deployment concerns new events and later periods;
3. Method: newly written replication attempt scoped to Table III using the current public artifact, a paper-code-data-label traceability audit, and row-, event-, and purged forward-time evaluation;
4. Result: `[PENDING FROZEN EXPERIMENTS]`;
5. Meaning and limitation: `[PENDING]`; no legal determination, real-market prevalence, daily false-alert or deployment claim.

## 1. Introduction

- Financial harm and pump-and-dump detection;
- why adjacent windows from one event are not independent deployment cases;
- one RQ and no claim-presupposing language;
- contributions limited to an open replication attempt, evaluation sensitivity, event-level uncertainty and explicit construct boundaries.

## 2. Related Work

- original La Morgia et al. benchmark;
- later crypto pump detection and class-imbalance studies;
- grouped and temporal evaluation in financial ML;
- closest-work table and precise remaining gap.

## 3. Data, Artifact Rerun and Replication Scope

- source, licence, hashes and features;
- event/time structure and label prevalence;
- released-code configuration and paper-reported tree constraints kept separate;
- paper/code/data version differences and attempts to recover the paper-era artifact;
- scoped aggregate P/R/F1 output match between the released script and the new implementation on the current matrices; AP is new-implementation-only;
- what is and is not redistributed.

## 4. Evaluation Protocol

- S0 non-shuffled row-level stratified cross-validation with event/time mixing;
- S1 event-exclusive;
- S2 outcome-label-free (`gt`-free) purged time-forward split assignment, with one primary common-calendar checkpoint and four dependent sensitivity checkpoints;
- models, threshold discipline, metrics and uncertainty;
- invariants and no-overwrite artifacts.

## 5. Results

- published Table III, current-artifact rerun and paper-reported-tree-constraint sensitivity table;
- three evaluation families;
- forward-window distribution and intervals;
- event detection/delay and feature ablations;
- robustness and coverage loss.

## 6. Error Analysis and Discussion

- benchmark-label false positives and false negatives;
- event heterogeneity and time drift;
- what a small/null difference would mean;
- what the study cannot establish.
- why event-centred ±24h windows are not a natural deployment stream.

## 7. Reproducibility, Ethics and Limitations

- public third-party market-feature matrices and event metadata; no raw message text is analysed; licence and ethics scope remain explicit;
- no identification or legal adjudication;
- code/artifact release;
- author and AI-assistance disclosure under venue policy.

## 8. Conclusion

One evidence-backed answer to the locked RQ; no expansion into Chinese NLP or LLM experiments.
