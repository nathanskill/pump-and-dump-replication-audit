# Gate 0 common-calendar forward design v3

Status: `STRUCTURAL PASS / FORMAL MODEL RUNS PENDING`

This artifact replaces the frequency-specific row-quantile cutoffs as the candidate formal forward design. It uses the 326 event identifiers present at all three frequencies and applies the same calendar cutoff and event partition to 25S, 15S and 5S.

## Frozen roles

| Nominal anchor rank | Role | Calendar cutoff | Train / test / purged events | Positive train / test / purged events after disclosed pilot inspection |
|---:|---|---|---:|---:|
| 40% | sensitivity | 2019-05-26 06:30:16.250 | 129 / 195 / 2 | 125 / 190 / 2 |
| 50% | sensitivity | 2019-08-02 07:00:58.750 | 162 / 162 / 2 | 158 / 157 / 2 |
| 60% | sensitivity | 2019-11-30 07:32:02.500 | 195 / 131 / 0 | 190 / 127 / 0 |
| 70% | sensitivity | 2020-03-25 03:58:20.000 | 226 / 97 / 3 | 221 / 93 / 3 |
| 80% | **primary** | 2020-06-20 04:00:35.000 | 260 / 66 / 0 | 253 / 64 / 0 |

The percentages are nominal ranks of canonical event anchors; for example, the primary training side contains 260/326 = 79.75% of common events. They are not exact row percentages.

## Evidence boundary

- The assignment rules use event identity and time but do not reference `gt`; this is narrower than claiming labels were unseen. The same run reads `gt` only after assignments are built to record positive-event diagnostics.
- Positive-event counts were inspected during the Gate 0 feasibility pilot. This design is therefore not described as preregistered, blinded or prospectively label-unseen. All five checkpoints, including the 80% primary, are now retained and may not be dropped based on labels or model scores.
- Training windows expand and the forward test tails contract. The test sets are nested and dependent, so the five checkpoints are reported separately and never pooled as independent folds or replicates.
- `event_overlap=0` proves only that an identical `pump_index` is not assigned to both train and test. It does not prove that near-duplicate activity or different identifiers for one underlying episode have been removed.
- Average Precision is prevalence-sensitive. It is interpreted within frequency and checkpoint, with prevalence reported; AP values are not directly ranked across 25S/15S/5S or treated as an independent time trend across nested checkpoints.
- The canonical anchor is the midpoint of the union event interval across frequencies, not an externally verified announcement time. Event 261 (`BNT`) has a 24,220-second cross-frequency start jitter and remains a named QC item.

## Reproducibility trail

- Script: `../../src/audit_common_forward.py`
- Script SHA-256: `702d56edde302b2f63777f8c70c520de3c9ebe7010e0801722fb2ab56622fc9c`
- Main window table SHA-256: `144114f343e381f44c4739c5a0aea08f9ae19601ea14825529b70c89924c3f1e`
- Environment and command: `run_metadata.json`
- Input hashes: `input_manifest.csv`
- Output hashes: `output_manifest.csv`
- Frequency-specific excluded IDs: `excluded_noncommon_event_manifest.csv`

Three split-invariant tests pass. Formal event-exclusive/forward model runs, event metric definitions, thresholds, uncertainty intervals and paper claims remain pending.
