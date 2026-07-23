# Pump-and-Dump Replication & Evaluation-Sensitivity Audit

Status: `FORMAL RUNS COMPLETE (S0 / S1 / S2 + time-feature ablation) / MANUSCRIPT IN PREPARATION / NOT SUBMITTED`

Working title (neutral while the 2020 published table remains unresolved):

> A Replication Attempt and Evaluation-Sensitivity Audit of "Pump and Dumps in the Bitcoin Era"

This repository contains a newly written, independent re-implementation and evaluation audit of the random-forest detection baseline released with:

> M. La Morgia, A. Mei, F. Sassi, J. Stefa, *Pump and Dumps in the Bitcoin Era: Real Time Detection of Cryptocurrency Market Manipulations*, ICCCN 2020. DOI: [10.1109/ICCCN49398.2020.9209660](https://doi.org/10.1109/ICCCN49398.2020.9209660)
> Upstream repository: [SystemsLab-Sapienza/pump-and-dump-dataset](https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset) (pinned commit `d71250d4cb055dde2d415c8cba38a0dcd6eb6e16`)

## What this study does

1. **Replication attempt**: re-implement the released RF baseline from scratch and compare against the upstream released script's aggregate precision/recall/F1 at the 5s/15s/25s feature frequencies.
2. **Evaluation-sensitivity audit**: examine how conclusions change between row-level, event-exclusive, and common-calendar forward-time evaluation on the same released artifacts, with event-level metrics specified before freezing.

## Current evidence state (honest boundary)

- **Verified**: the aggregate precision, recall and F1 of this repository's newly written RF implementation match the outputs of the released upstream script at 25S/15S/5S on the released feature matrices; purged time-forward split structures have manifests and verification artifacts; a documented initial citation-forward screen is complete.
- **Formal results (frozen protocol, commit `c2736ed`; archived run configs carry the pre-rewrite identifier `23089ce` — see `protocol/amendment_A3_metadata_rewrite.md` for the authoritative map)**: three evaluation families on the identical 326-common-event universe — pooled OOF AP 0.9649/0.9462/0.9025 (S0 row-level), 0.9636/0.9466/0.9007 (S1 event-exclusive), 0.9781/0.9572/0.9072 (S2 forward @80%, 25S/15S/5S); event-level EDR and delay under the frozen specification; time-of-day ablation lowers forward AP by 0.010–0.028. See `artifacts/formal_*`.
- **Frozen**: the event-level outcome specification (benchmark onset bins, training-side thresholds, cooldown handling, exact/post-onset/lead windows, delay, benchmark-negative episodes) is locked in `protocol/locked_protocol_v0.2.md`; the 20-test suite passed before and after the formal runs.
- **Unresolved**: exact replication of the published Table III — the paper's described parameters, the released code, and the post-paper released matrices differ; the public upstream repository does not expose an end-to-end label-generation process.
- **Not completed**: manuscript, preprint, formal submission, peer review, or publication. No claim of priority or of being the first replication is made.

The upstream feature matrices cover approximately ±24 hours around known events. Without an additional lawful natural-market background stream, this study does not estimate deployment prevalence, real-world calibration, daily false-alert load, or reviewer workload.

## Repository layout

- `protocol/` — locked protocol, Gate 0 checklist, claim register, source & licence audit
- `src/` — newly written implementation and audit scripts (no upstream code copied)
- `tests/` — split-invariant and protocol unit tests
- `artifacts/` — run manifests, configurations, aggregate metrics, split/partition manifests, environment records
- `paper/` — manuscript outline (work in progress)

## Reproducing the results

1. Clone the upstream dataset repository at pinned commit `d71250d` and verify file hashes against `protocol/source_and_licence_audit_v0.1.md` and the `input_manifest.json` files under `artifacts/`.
2. Install pinned dependencies: `python3.9 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
3. Run the test suite: `.venv/bin/python -m unittest discover -s tests` (20 tests; upstream-dependent invariants auto-skip if the matrices are absent; set `PUMP_AUDIT_UPSTREAM=/path/to/pump-and-dump-dataset` to enable them).
4. Re-run the formal experiments with explicit flags (the runners refuse to overwrite committed artifacts — point `--output-root` at a fresh directory):
   - `.venv/bin/python src/run_formal_cv.py --upstream /path/to/pump-and-dump-dataset --output-root artifacts_rerun`
   - `.venv/bin/python src/run_formal_forward.py --upstream /path/to/pump-and-dump-dataset --output-root artifacts_rerun`
   - `.venv/bin/python src/run_formal_forward.py --drop-time-features --upstream /path/to/pump-and-dump-dataset --output-root artifacts_rerun_ablation`
5. Compare regenerated `summary.csv`/`metrics.json` against the committed artifacts. Note: fresh runs stamp the current freeze SHA (`c2736ed`); archived configs carry the pre-rewrite identifier (`23089ce`) — amendment A3 is the authoritative map.

## Claims → artifacts map

| Manuscript claim | Artifact directory |
|---|---|
| §4.1 code-level replication (released script vs re-implementation) | `gate0_upstream_stdout_capture_20260721`, `gate0_released_code_rf_all_v2_20260721`, `gate0_baseline_comparison_20260721` |
| §4.2 Table III traceability (paper-described configuration) | `gate0_paper_described_rf_all_20260721` |
| §4.3 S0 / S1 family comparison | `formal_s1_s0_v1_20260722` |
| §4.3–4.4 S2 forward checkpoints | `formal_forward_v1_20260722` |
| §4.5 / Appendix A time-of-day ablation | `formal_forward_ablation_v1_20260722` |

## Redistribution boundary

This repository deliberately does **not** re-upload the upstream labelled feature matrices, raw transaction records, Telegram group list, or event file. To reproduce, acquire the upstream inputs from the original repository at the pinned commit and verify against the hashes in `protocol/source_and_licence_audit_v0.1.md` and the run manifests. Upstream notices are preserved in `THIRD_PARTY_NOTICES.md`. Large per-row prediction files are reproducibility evidence generated locally and are not committed.

## Related work by the same author

- [evidence-separated-trading-screening](https://github.com/nathanskill/evidence-separated-trading-screening) — protocol-stage research line on evidence-separated screening of Chinese-language trading promotions (REF-2026-002). The two lines share the same methodological commitments: held-out/forward-time evaluation, leakage control, and pre-declared claim boundaries.

## License

Newly written code and documentation in this repository: MIT (see `LICENSE`). Upstream materials remain under their own terms (see `THIRD_PARTY_NOTICES.md`).
