# Pump-and-Dump Replication & Evaluation-Sensitivity Audit

Status: `FORMAL RUNS COMPLETE (S0 / S1 / S2 + ablation + A4 addendum) · MANUSCRIPT DRAFT v0.5 · LaTeX SUBMISSION SOURCE PREPARED (FC 2027) · NOT SUBMITTED · NOT PEER REVIEWED`

Working title:

> Replication and Evaluation-Sensitivity Audit of "Pump and Dumps in the Bitcoin Era"

An independent, newly written re-implementation and evaluation audit of the random-forest detection baseline released with:

> M. La Morgia, A. Mei, F. Sassi, J. Stefa, *Pump and Dumps in the Bitcoin Era: Real Time Detection of Cryptocurrency Market Manipulations*, ICCCN 2020. DOI: [10.1109/ICCCN49398.2020.9209660](https://doi.org/10.1109/ICCCN49398.2020.9209660)
> Upstream repository: [SystemsLab-Sapienza/pump-and-dump-dataset](https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset) (pinned commit `d71250d4cb055dde2d415c8cba38a0dcd6eb6e16`)

## The question

Reported scores for cryptocurrency pump-and-dump classifiers are usually produced by row-level cross-validation, in which rows sampled seconds apart from the same event can fall on both sides of a split. Whether that choice matters for this widely reused baseline had not been measured on the released artifact itself. This project asks one question: to what extent can the released baseline's results be traced, replicated, and shown to survive a change of evaluation unit? Two parts follow from it — a replication attempt against the released classifier script, and a sensitivity audit across row-level (S0), event-exclusive (S1) and purged forward-time (S2) evaluation on an identical event universe, with the event-level outcome specification frozen before any outer run.

## What has been done

All numbers below are recorded in hash-manifested artifact directories under `artifacts/`; the manuscript cites the same directories section by section.

**1. The re-implementation reproduces the released script exactly.** Aggregate precision, recall and F1 match the released classifier script to every reported decimal at all three feature frequencies on the released matrices: 0.9658 / 0.8896 / 0.9261 at 25 s, 0.9679 / 0.8549 / 0.9079 at 15 s, 0.9433 / 0.7350 / 0.8262 at 5 s (`gate0_baseline_comparison_20260721`).

**2. The published Table III could not be recovered.** The paper-described parameters, the released code and the post-paper released matrices differ, and the upstream repository does not expose the manual label-generation step. The gap is documented descriptively; its cause is left open. The same authors' journal extension tracks the released artifact far more closely than Table III does (`gate0_paper_described_rf_all_20260721`).

**3. Discrimination is largely insensitive to the evaluation family.** On the identical universe of 326 common events, pooled out-of-fold average precision with 95% event-cluster bootstrap intervals:

| Family | 25 s | 15 s | 5 s |
|---|---|---|---|
| S0 row-level 5-fold | 0.9649 [0.949, 0.979] | 0.9462 [0.925, 0.965] | 0.9025 [0.876, 0.929] |
| S1 event-exclusive 5-fold | 0.9636 [0.947, 0.978] | 0.9466 [0.925, 0.966] | 0.9007 [0.873, 0.927] |
| S2 forward @80% (primary) | 0.9781 [0.948, 0.999] | 0.9572 [0.917, 0.991] | 0.9072 [0.845, 0.957] |

Under a shared event resample, the paired ΔAP(S1 − S0) interval covers zero at every frequency (−0.0013 [−0.0039, +0.0009] at 25 s; +0.0004 [−0.0022, +0.0030] at 15 s; −0.0017 [−0.0051, +0.0012] at 5 s). The forward family's nominally higher score is a test-composition effect, not a family effect: S1's predictions restricted to the 66 S2 primary test events give 0.9785 / 0.9591 / 0.9148 against S2's 0.9781 / 0.9572 / 0.9072 (`formal_s1_s0_v1_20260722`, `formal_forward_v1_20260722`, `a4_addendum_v1_20260723`).

**4. Event-level detection degrades at the finest frequency — the weakness row-level scores hide.** At the released decision threshold, the event detection rate within 120 s falls from 0.922 (25 s) to 0.641 (5 s) at the primary forward checkpoint (59/64 vs 41/64 eligible test events), and from 0.886 to 0.710 pooled across S1 folds (281/317 vs 225/317). Median detection delay equals one bin width at every frequency, the interval-censored minimum (`a4_addendum_v1_20260723`).

**5. The four time-of-day features are a small increment, not a shortcut.** Ablating them lowers forward AP by between 0.010 and 0.028 across all fifteen frequency-by-checkpoint combinations (`formal_forward_ablation_v1_20260722`). By protocol this is descriptive: a drop does not prove leakage, and a null effect does not prove its absence.

**6. The manuscript exists and is submission-ready in source form.** `paper/manuscript_draft_v0.5.md` (2 August 2026) is a complete draft — abstract through references, 28 citations, two figures — rendered to PDF alongside its two predecessors. `paper/latex/` holds an LNCS conversion (`main.tex`) with a single-toggle anonymous/named build for Financial Cryptography 2027 (submission deadline 17 September 2026) and an anonymisation ledger recording every difference between the builds. Nothing has been submitted anywhere.

## The discipline

The protocol was frozen before the outer runs, and every later change is a numbered public amendment rather than a silent edit.

- `protocol/locked_protocol_v0.2.md` fixes the evaluation families, the event-level outcome specification (benchmark onset bins, training-side thresholds, cooldown handling, exact/post-onset/lead windows, interval-censored delay, benchmark-negative episodes) and the prohibited-claims list. The freeze commit is `c2736ed`; archived run configurations carry its pre-rewrite identifier `23089ce`, and `protocol/amendment_A3_metadata_rewrite.md` is the authoritative map between the two, including the tree-hash verification that file contents were untouched by the rewrite.
- Amendment A1 permanently suspends every claim that would have needed upstream author clarification and prohibits the wordings "failed replication" and "not reproducible". Amendment A2 records that a provenance inquiry was sent to the upstream corresponding author on 22 July 2026 (dated 23 July AEST), after results were complete, with a pre-declared rule: no reply after 14 days is recorded as "no response at the time of submission" and re-checked before camera-ready. Non-reply neither weakens any suspension nor proves anything about the original work.
- Amendment A4 was committed as a specification before any of its computations ran; its outputs (the bootstrap intervals, paired ΔAP and matched-universe comparison above) introduce no new models, thresholds or claims.
- The 20-test suite (split invariants, outcome-specification unit tests) passed before and after the formal runs.
- Published tags are records. `v0.1.0-protocol-freeze` anchors the protocol, `v0.2.0-results-freeze` the results, and `v0.2.1-results-freeze` — identical result artifacts plus a corrected `CITATION.cff` — is the archival target. The superseded tags stay in place unmoved.

## What is not claimed

- No claim of priority or of being the first replication.
- No adjudication of the upstream authors' results. The Table III gap is reported as a traceability finding, not a failed replication.
- No deployment claim of any kind. The upstream matrices cover roughly ±24 hours around known events; without a lawful natural-market background stream this study cannot estimate real-world prevalence, calibration, daily false-alert load or reviewer workload, and the frozen protocol prohibits those phrases outright. Benchmark-negative episode rates on these curated windows are never a real-world false-alarm rate.
- `gt=0` is never read as confirmed absence of a pump; label provenance is unresolved from public materials.
- Peer review, publication and the Zenodo deposit have not happened. The draft is complete; its claims are unreviewed.

## Reproducing the results

1. Clone the upstream dataset repository at pinned commit `d71250d` and verify file hashes against `protocol/source_and_licence_audit_v0.1.md` and the `input_manifest.json` files under `artifacts/`.
2. Install pinned dependencies: `python3.9 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
3. Run the test suite: `.venv/bin/python -m unittest discover -s tests` (20 tests; upstream-dependent invariants auto-skip if the matrices are absent; set `PUMP_AUDIT_UPSTREAM=/path/to/pump-and-dump-dataset` to enable them).
4. Re-run the formal experiments with explicit flags. The runners refuse to overwrite committed artifacts, so point `--output-root` at a fresh directory:
   - `.venv/bin/python src/run_formal_cv.py --upstream /path/to/pump-and-dump-dataset --output-root artifacts_rerun`
   - `.venv/bin/python src/run_formal_forward.py --upstream /path/to/pump-and-dump-dataset --output-root artifacts_rerun`
   - `.venv/bin/python src/run_formal_forward.py --drop-time-features --upstream /path/to/pump-and-dump-dataset --output-root artifacts_rerun_ablation`
5. Compare regenerated `summary.csv` / `metrics.json` against the committed artifacts. Fresh runs stamp the current freeze SHA (`c2736ed`); archived configs carry the pre-rewrite identifier (`23089ce`) — amendment A3 is the authoritative map.

Per-row prediction files are reproducibility evidence generated locally and are not committed; regenerating the figures in `paper/figures/` therefore requires first re-running `src/run_formal_cv.py` and `src/run_formal_forward.py` (then `src/make_figures.py`).

## Claims → artifacts map

| Manuscript claim (draft v0.5) | Artifact directory |
|---|---|
| §4.1 code-level replication (released script vs re-implementation) | `gate0_upstream_stdout_capture_20260721`, `gate0_released_code_rf_all_v2_20260721`, `gate0_baseline_comparison_20260721` |
| §4.2 Table III traceability (paper-described configuration; journal rows) | `gate0_paper_described_rf_all_20260721`, `gate0_baseline_comparison_20260721` |
| §4.3 S0 / S1 family comparison | `formal_s1_s0_v1_20260722` |
| §4.3–4.4 S2 forward checkpoints | `formal_forward_v1_20260722` |
| §4.3 bootstrap CIs, paired ΔAP, matched-universe comparison; §4.4 full outcome set | `a4_addendum_v1_20260723` |
| §4.5 / Appendix A time-of-day ablation | `formal_forward_ablation_v1_20260722` |

## Repository layout

- `protocol/` — locked protocol v0.1/v0.2, Gate 0 checklist, claim register, source & licence audit, amendments A1–A4
- `src/` — newly written implementation, audit runners, figure generation (no upstream code copied)
- `tests/` — split-invariant and outcome-specification unit tests
- `artifacts/` — run manifests, frozen configurations, aggregate metrics, split manifests, environment records
- `paper/` — manuscript drafts v0.3–v0.5 (Markdown + rendered PDFs), figures, and the LNCS LaTeX submission source with anonymisation ledger (`paper/latex/ANONYMIZATION_NOTES.md`)

## Archival and release path

The intended venue is Financial Cryptography and Data Security 2027. The results-complete release `v0.2.1-results-freeze` is archived under a persistent DOI:

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21805707.svg)](https://doi.org/10.5281/zenodo.21805707)

No step of the plan depends on a preprint server accepting or endorsing the author.

1. **Zenodo (primary).** Publish a GitHub release of tag `v0.2.1-results-freeze`; Zenodo archives it and reads `CITATION.cff`. The two earlier tags are not the archival target: `v0.2.0-results-freeze` carries the same result artifacts but a superseded `CITATION.cff` that would make Zenodo mint the record under the wrong version. `v0.2.1` exists to fix that without rewriting a published tag. Zenodo has no endorsement or affiliation gate ([policies](https://about.zenodo.org/policies/), checked 2026-08-02). Known limitation: Zenodo is not indexed by Google Scholar ([Zenodo FAQ](https://support.zenodo.org/help/en-gb/18-general/61-is-zenodo-indexed-by-google-scholar), checked 2026-08-02), so Scholar discoverability has to come from the venue, not the DOI.
2. **Cryptology ePrint Archive (optional, non-blocking).** Posting does not prevent venue submission ([operations](https://eprint.iacr.org/operations.html), checked 2026-08-02), but this work contains no cryptographic construction — its fit is venue adjacency, and rejection as out of scope is a real possibility. Optional upside, never a dependency.
3. **arXiv (contingent only).** Since 21 January 2026 automatic endorsement requires both an institutional email and prior authorship in the target domain ([arXiv blog](https://blog.arxiv.org/2026/01/21/attention-authors-updated-endorsement-policy/), checked 2026-08-02); the author meets neither, so arXiv is reachable only through a third party's endorsement and nothing waits on it.

Posting in non-anonymous form conflicts with none of this: the FC 2027 call explicitly permits submitted papers to exist online non-anonymously ([cfp](https://ifca.ai/fc27/cfp.html), checked 2026-08-02).

## Redistribution boundary

This repository deliberately does not re-upload the upstream labelled feature matrices, raw transaction records, Telegram group list, or event file. Reproducers acquire the upstream inputs from the original repository at the pinned commit and verify them against the hashes in `protocol/source_and_licence_audit_v0.1.md` and the run manifests. Upstream notices are preserved in `THIRD_PARTY_NOTICES.md`.

## Related work by the same author

- [evidence-separated-trading-screening](https://github.com/nathanskill/evidence-separated-trading-screening) — protocol-stage research line on evidence-separated screening of Chinese-language trading promotions (REF-2026-002). The two lines share the same methodological commitments: held-out and forward-time evaluation, leakage control, and pre-declared claim boundaries.

## License

Newly written code and documentation in this repository: MIT (see `LICENSE`). Upstream materials remain under their own terms (see `THIRD_PARTY_NOTICES.md`).
