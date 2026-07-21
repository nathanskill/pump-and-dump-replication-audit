# REF-2026-016 Protocol v0.2

> Status: `FROZEN CANDIDATE — the commit hash of this file in the public
> repository is the freeze marker; outer test runs may only cite that commit.`
> Supersedes `locked_protocol_v0.1.md`. The only substantive change is that the
> event-level outcome specification is now frozen and implemented with unit
> tests (`src/event_metrics.py`, `tests/test_event_metrics.py`). Results are
> not yet known under the full protocol.

## Research questions

1. To what extent can the 2020 Table III market-feature result be traced and replicated using a newly written, tested and openly documented implementation together with the currently public artifact?
2. Within the current public event-centred artifact, how sensitive are the reported discrimination and event-detection results to non-shuffled row-level stratified CV, event-exclusive CV and outcome-label-free (`gt`-free) purged time-forward evaluation?

## Data

- Public market-feature matrices at 5-second, 15-second, and 25-second aggregation;
- `pump_index` is the event grouping key; `date` defines temporal order; `gt` is an outcome label and is prohibited from split membership logic;
- Label provenance remains a Gate 0 question: the upstream README describes manual pump-start labelling, while the public feature script initializes `gt=0` and does not expose the later manual label-generation step;
- The matrices cover windows around known pump events rather than a natural continuous market stream. Unless a separate lawful background stream passes Gate 0, no deployment prevalence, real-world false-alert, workload or calibration claim is permitted.

## Models

- Released-code baseline: Random Forest matching `classifier.py` (`n_estimators=200`, `max_depth=5`, default `min_samples_leaf`, `random_state=1`);
- Paper-described baseline: Random Forest matching the article text (`n_estimators=200`, `max_depth=4`, `min_samples_leaf=6`); a traceability sensitivity, not silently interchangeable with the released-code baseline;
- Optional sensitivity: regularized logistic regression only if Gate 0 records the separate question it answers; preprocessing and tuning remain confined to training/validation data.

## Evaluation families

- `S0_ROW_5FOLD`: upstream-style non-shuffled stratified row-level cross-validation; it mixes event/time contexts and is not described as a random split. Because rows of one event can appear in both train and test, `S0` reports chunk-level replication metrics only — no event-level detection or delay;
- `S1_EVENT_5FOLD`: event-exclusive GroupKFold;
- `S2_FORWARD_PURGED`: common-calendar, event-exclusive and purged forward assignment that does not read `gt`; the 80% checkpoint is primary and the 40/50/60/70% expanding checkpoints are dependent sensitivity analyses, not independent folds or replicates.

## Frozen event-level outcome specification

Implemented in `src/event_metrics.py`; every rule below is covered by
`tests/test_event_metrics.py`.

### Units and reference time

- 25S, 15S and 5S are evaluated separately and never pooled;
- the event unit is `pump_index`; an event is **eligible** only if its group contains exactly one `gt=1` row. Current matrices: 317 eligible events and 10 no-positive groups per frequency (test-enforced invariant). No-positive groups stay out of the event denominator and are **not** negative events;
- `t0(e, f)` is the `date` of the unique `gt=1` row and is only a **benchmark reference onset-bin start**, not verified economic truth;
- `date` is a bin label. With bin width `delta_f`, row information is earliest available at `t_available = date + delta_f`; onset-bin delay is therefore interval-censored and never reported as exactly zero.

### Thresholds (both frozen; no outer-test tuning)

1. **Replication anchor `tau = 0.5`** — connects Table III and the released script's `predict()`;
2. **Training-calibrated `tau*`** — selected only from outer-training out-of-fold probabilities (`S1`: event-grouped inner CV; `S2`: expanding-time inner validation); candidates are the unique out-of-fold scores plus 0.5; the criterion is chunk-level F1, ties resolving to the **higher** threshold; the outer test is evaluated once.

### Alert aggregation

Within each held-out `pump_index`, candidate alerts (`score >= tau`) are processed in strict time order **from the full window start**; after an emitted alert a fixed 30-minute cooldown (from the original paper, not re-tuned) suppresses all crossings with `t < last_emitted + 30 min`. Starting the clock at the window start is mandatory so that an early alert legitimately suppressing an onset-adjacent alert is captured, not bypassed.

### Detection, lead and delay

- `EDR_exact` = share of eligible events with at least one emitted alert sourced from the `gt=1` row (benchmark-faithful hit rate, not a real-market detection rate);
- `EDR@30s`, `EDR@60s`, `EDR@120s` = share of eligible events with an emitted alert whose `t_available` lies in `(t0, t0 + H]`; all three horizons are always reported; adjacent `gt=0` rows are **not** relabelled as true positives;
- `Lead@30s / Lead@60s / Lead@120s` count only emitted alerts with `t_available` in `[t0 − L, t0]` and are reported separately — lead alerts are never merged into post-onset detection;
- delay `d_e = min(t_available) − t0` over qualifying alerts in `(t0, t0 + 120s]`, reported as median, IQR, 90th percentile **together with** `n_detected / n_eligible` to avoid survivor bias.

### Benchmark alert burden and permitted wording

Emitted alerts sourced from `gt=0` rows are **benchmark-negative alert episodes**; report per-event mean, median, distribution and a 95% event-cluster bootstrap interval (resampling `pump_index` clusters, never rows; fixed seed and `n_boot` recorded in the run config).

| Situation | Permitted wording |
|---|---|
| Alert from a `gt=0` row | benchmark-label false-positive chunk/alert |
| Unique `gt=1` row not alerted | benchmark-label false negative at the onset chunk |
| No alert within `H` | event not detected within the prespecified `H`-second horizon |
| Alert elsewhere in the window | off-onset benchmark alert (possibly unlabelled anomaly; no real-false-alarm assertion) |
| No hit in the whole group | benchmark event miss |

The phrases `real false-alarm rate`, `daily false alerts`, `deployment specificity` and `analyst workload` are prohibited. One onset-adjacent alert may simultaneously be an `EDR@120s` hit and a benchmark-label FP; the two readings coexist and are reported as such.

### Suspended while provenance is unresolved

1. The 10 no-positive groups are not treated as negative events;
2. Telegram scheduled times are not used as `t0`;
3. Only benchmark-bin delay proxies are reported, never "true onset delay";
4. No cross-`pump_index`, per-symbol market-wide cooldown;
5. No real FP/FN, event prevalence, daily alert volume or calibration claims;
6. `gt=0` is never interpreted as confirmed absence of a pump;
7. All of 30/60/120s are reported; no single window is promoted as the headline.

## Outcomes

- Primary: Average Precision within each frequency; report each frequency's prevalence and do not interpret AP differences across 25S/15S/5S as direct model-performance differences;
- Event-level: the frozen specification above;
- Uncertainty: pump-event cluster intervals for each evaluation result; overlapping forward checkpoints are reported separately and never pooled as independent replicates;
- Deployment calibration/alert burden: prohibited for the A-level event-centred study; enabled only if a separate natural-background protocol passes Gate 0;
- Secondary: precision, recall, F1 and ROC-AUC.

## Analysis discipline

- Split definitions, model list, thresholds and primary outcomes are frozen as of this file's release commit; outer test runs may begin only after that commit exists and must cite it;
- Gate 0 feasibility work inspected positive-event counts at all five forward checkpoints. Split assignment itself did not read `gt`, but this pilot means the checkpoints are not presented as preregistered or label-unseen. All five are retained; none may be removed based on labels or performance;
- After this disclosed pilot, test labels are used only for frozen benchmark scoring and error analysis — never for model, threshold or checkpoint selection;
- Every run writes a non-overwriting config, seed, environment, fold manifest, prediction file, metric file and artifact hash;
- All frequencies and all five forward checkpoints are reported, including weak or null results;
- Comparisons across evaluation families are descriptive sensitivity comparisons, not a causal estimate of a single split effect;
- Upstream data are not redistributed unless the licence audit explicitly authorises it;
- The upstream author artifact/label-provenance query and its outcome (reply, no reply, or unavailability) are recorded verbatim in the evidence log before submission; freeze of this protocol does not depend on the reply, but provenance-dependent claims stay suspended until it is resolved.

## Claims prohibited before completion

- severe leakage; performance collapse; deployment readiness;
- real-market prevalence, daily false alerts or analyst workload from the event-centred matrices;
- independent replication; first replication; state of the art;
- published, peer reviewed, accepted, or submitted.
