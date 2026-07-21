# REF-2026-016 Claim Register v0.1

| Claim | State | Allowed wording now | Upgrade evidence |
|---|---|---|---|
| Public feature matrices and upstream code are locally available | Verified | locally archived upstream snapshot | source, commit and hashes |
| Reduced audit runs | Verified | single-team local exploratory run | existing logs/manifests/verifier |
| Strict one-cutoff forward split exists | Verified | one outcome-label-free (`gt`-free) purged time-forward engineering anchor | v2 manifest and invariant verification |
| Row-level evaluation materially overstates performance | Unknown | research question only | full frozen protocol, intervals and robustness |
| Five structurally valid forward checkpoints exist | Verified for split structure | one primary and four dependent sensitivity checkpoints use common calendar cutoffs, are event-disjoint across train/test and satisfy strict time order at all three frequencies; positive counts were inspected during the Gate 0 pilot | frozen model-run manifests and event-level results |
| Newly written code matches the released script's aggregate outputs on released matrices | Verified | aggregate P/R/F1 match at 25S/15S/5S; AP is new-implementation-only | E-103, captured upstream stdout and full artifacts |
| Published Table III has been exactly replicated | Not achieved | paper/code/data traceability remains unresolved | paper-era matrices, labels and exact configuration plus a successful result within predeclared tolerance |
| Current public script can be rerun on the current matrices | Verified in recorded local environment | current public script was successfully rerun locally; this is separate from label regeneration and Table III replication | frozen commit and dependency lock plus a one-command clean Linux/Docker rerun with complete output verification |
| Manuscript is a preprint | Not achieved | manuscript in production | stable preprint URL/DOI |
| Manuscript is submitted | Not achieved | target venue under review internally | submission receipt |
| Work is peer reviewed or published | Not achieved | never imply this | journal decision and publication record |
| Work validates the Chinese NLP proposal | False inference | separate methodological foundation paper | a later authorised Chinese-text study |
| Existing matrices represent natural market flow | False | known-event-centred ±24h windows | a separately designed lawful natural-background stream |
| Existing matrices estimate daily false alerts/workload | Not supported | do not report | B-level background-stream protocol and valid labels/uncertainty |
| This is the first time-split pump study | False/overbroad | no such claim | impossible given existing temporal studies |
| No prior replication of La Morgia exists | Pending verification | whether a sufficient prior replication exists is not yet determined | documented citation-forward search and ReScience fit check |
| Public labels can be rebuilt end to end | Pending verification | the README describes manual pump-start labelling, but the public feature code initializes `gt=0` and does not expose the manual label-generation step | provenance documentation, author clarification and a reproducible rebuild path |
