# REF-2026-016 Protocol v0.1

> Status: `CANDIDATE — FREEZE AFTER GATE 0`  
> Results are not yet known under the full protocol.

## Research questions

1. To what extent can the 2020 Table III market-feature result be traced and replicated using a newly written, tested and openly documented implementation together with the currently public artifact?
2. Within the current public event-centred artifact, how sensitive are the reported discrimination and event-detection results to non-shuffled row-level stratified CV, event-exclusive CV and outcome-label-free (`gt`-free) purged time-forward evaluation?

## Data

- Public market-feature matrices at 5-second, 15-second, and 25-second aggregation;
- `pump_index` is the event grouping key;
- `date` defines temporal order;
- `gt` is an outcome label and is prohibited from split membership logic.
- Label provenance remains a Gate 0 question: the upstream README describes manual pump-start labelling, while the public feature script initializes `gt=0` and does not expose the later manual label-generation step. Ten event groups in the current matrices have no positive label.
- The matrices cover windows around known pump events rather than a natural continuous market stream. Unless a separate lawful background stream passes Gate 0, no deployment prevalence, real-world false-alert, workload or calibration claim is permitted.

## Models

- Released-code baseline: Random Forest matching `classifier.py` (`n_estimators=200`, `max_depth=5`, default `min_samples_leaf`, `random_state=1`);
- Paper-described baseline: Random Forest matching the article text (`n_estimators=200`, `max_depth=4`, `min_samples_leaf=6`); this is a traceability sensitivity, not silently interchangeable with the released-code baseline;
- Optional sensitivity: regularized logistic regression only if Gate 0 records the separate question it answers; preprocessing and tuning remain confined to training/validation data.

## Evaluation families

- `S0_ROW_5FOLD`: upstream-style non-shuffled stratified row-level cross-validation; it mixes event/time contexts and is not described as a random split;
- `S1_EVENT_5FOLD`: event-exclusive GroupKFold;
- `S2_FORWARD_PURGED`: common-calendar, event-exclusive and purged forward assignment that does not read `gt`; the 80% checkpoint is primary and the 40/50/60/70% expanding checkpoints are dependent sensitivity analyses, not independent folds or replicates.

## Outcomes

- Primary: Average Precision within each frequency; report each frequency's prevalence and do not interpret AP differences across 25S/15S/5S as direct model-performance differences;
- Uncertainty: pump-event cluster intervals for each evaluation result; overlapping forward checkpoints are reported separately and are never pooled as independent replicates;
- Event-level candidate specification: `pump_index` is the event unit; only groups with exactly one `gt=1` enter the event denominator; the unique positive-bin `date` is a benchmark reference onset-bin start, not verified economic truth. Report fixed-threshold (`tau=0.5`) and training-calibrated sensitivity results, 30-minute cooldown aggregation, `EDR_exact`, `EDR@30/60/120s`, separate `Lead@30/60/120s`, delay conditional on `EDR@120s`, and benchmark-negative alert episodes. This remains a planned outcome until protocol v0.2 and tests freeze it; see E-106;
- Deployment calibration/alert burden: prohibited for the A-level event-centred study; enabled only if a separate natural-background protocol passes Gate 0;
- Secondary: precision, recall, F1 and ROC-AUC.

## Analysis discipline

- Split definitions, model list and primary outcomes freeze before the final runs;
- Gate 0 feasibility work inspected positive-event counts at all five forward checkpoints. Split assignment itself did not read `gt`, but this pilot means the checkpoints are not presented as preregistered or label-unseen. All five are now retained, and no checkpoint may be removed based on labels or performance;
- After this disclosed pilot, test labels may not be used for model, threshold or checkpoint selection; they are used only for the frozen benchmark scoring and error analysis;
- Every run writes a non-overwriting config, seed, environment, fold manifest, prediction file, metric file and artifact hash;
- All frequencies and all five forward checkpoints are reported, including weak or null results; the 80% checkpoint is primary and the four earlier overlapping checkpoints are sensitivity analyses;
- Comparisons across evaluation families are descriptive sensitivity comparisons, not a causal estimate of a single split effect;
- Upstream data are not redistributed unless the licence audit explicitly authorises it.

## Claims prohibited before completion

- severe leakage;
- performance collapse;
- deployment readiness;
- real-market prevalence, daily false alerts or analyst workload from the event-centred matrices;
- independent replication;
- state of the art;
- published, peer reviewed, accepted, or submitted.
