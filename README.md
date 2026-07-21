# Pump-and-Dump Replication & Evaluation-Sensitivity Audit

Status: `GATE 0 IN PROGRESS / RELEASED-CODE BASELINE PASSED / NO PAPER RESULT CLAIMED`

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
- **Candidate, not frozen**: event-level outcome metrics have a written pre-freeze specification (benchmark onset bins, training-side thresholds, cooldown handling, exact/post-onset/lead windows, delay, benchmark-negative episodes). Protocol v0.2 and unit tests must pass before outer test runs.
- **Unresolved**: exact replication of the published Table III — the paper's described parameters, the released code, and the post-paper released matrices differ; the public upstream repository does not expose an end-to-end label-generation process.
- **Not completed**: manuscript, preprint, formal submission, peer review, or publication. No claim of priority or of being the first replication is made.

The upstream feature matrices cover approximately ±24 hours around known events. Without an additional lawful natural-market background stream, this study does not estimate deployment prevalence, real-world calibration, daily false-alert load, or reviewer workload.

## Repository layout

- `protocol/` — locked protocol, Gate 0 checklist, claim register, source & licence audit
- `src/` — newly written implementation and audit scripts (no upstream code copied)
- `tests/` — split-invariant and protocol unit tests
- `artifacts/` — run manifests, configurations, aggregate metrics, split/partition manifests, environment records
- `paper/` — manuscript outline (work in progress)

## Redistribution boundary

This repository deliberately does **not** re-upload the upstream labelled feature matrices, raw transaction records, Telegram group list, or event file. To reproduce, acquire the upstream inputs from the original repository at the pinned commit and verify against the hashes in `protocol/source_and_licence_audit_v0.1.md` and the run manifests. Upstream notices are preserved in `THIRD_PARTY_NOTICES.md`. Large per-row prediction files are reproducibility evidence generated locally and are not committed.

## Related work by the same author

- [evidence-separated-trading-screening](https://github.com/nathanskill/evidence-separated-trading-screening) — protocol-stage research line on evidence-separated screening of Chinese-language trading promotions (REF-2026-002). The two lines share the same methodological commitments: held-out/forward-time evaluation, leakage control, and pre-declared claim boundaries.

## License

Newly written code and documentation in this repository: MIT (see `LICENSE`). Upstream materials remain under their own terms (see `THIRD_PARTY_NOTICES.md`).
