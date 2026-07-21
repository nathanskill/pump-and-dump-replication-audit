# Gate 0 Structural Audit — 2026-07-21

Status: `PARTIAL PASS / GATE 0 REMAINS OPEN`

## What was tested

- Loaded all three upstream labelled feature matrices (`25S`, `15S`, `5S`);
- hashed each compressed input;
- summarised rows, event groups, positive rows/events, date range and group-window length;
- built five predeclared row-time cutoffs (`40/50/60/70/80%`) using only `source_row`, `pump_index` and `date`;
- purged every event group that crossed a cutoff;
- checked zero train/test event overlap and strict `max(train date) < min(test date)`;
- attached `gt` only after partition construction to report feasibility diagnostics.

## Key findings

- All three matrices contain `327` event groups and `317` positive event groups.
- Median group coverage is about `47.9` hours, consistent with the upstream event-centred ±24-hour construction.
- All five candidate cutoffs are feasible at all three frequencies.
- The latest 80% cutoff still leaves 69–70 positive test events, and the earliest 40% cutoff leaves 223–232.
- Only one or two event groups are purged at each cutoff; train/test event overlap is zero and strict time order passes.
- At least one event group has a zero-hour observed span, and ten event groups have no positive labelled row. These are data-quality questions for the next Gate 0 audit, not reasons to silently drop rows.

## Files

- `structure_summary.json`
- `forward_cutoff_feasibility.csv`
- `input_manifest.csv`

## Test record

`python -m unittest discover -s REF-2026-016_public_pump_audit/tests -p 'test_*.py' -v`

Result: 2 tests passed. The tests confirm that a group straddling the cutoff is purged and that passing `gt` into the partition function is rejected.

## What this does not prove

- It does not reproduce the original Random Forest result;
- it does not establish novelty or ReScience C eligibility;
- it does not create a natural market background stream;
- it does not provide final paper metrics, calibration, real false-alert rates, a preprint or a submission.

