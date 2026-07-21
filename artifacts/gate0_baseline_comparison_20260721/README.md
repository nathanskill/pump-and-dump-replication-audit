# Gate 0 baseline comparison

Status: `CODE-LEVEL PASS / PAPER-TABLE REPLICATION UNRESOLVED`

## What was run

1. The released upstream `classifier.py` on the released feature matrices, with stdout, command, environment and hashes captured independently;
2. Nathan's newly written implementation using the released-code configuration (`200` trees, depth `5`, default leaf size, seed `1`, non-shuffled stratified 5-fold);
3. Nathan's newly written implementation using the tree constraints reported in the paper (`200` trees, depth `4`, minimum leaf size `6`) together with the released script's CV assumptions on the current extended matrices. This is not presented as the complete paper-era configuration.

The newly written implementation's aggregate precision, recall and F1 outputs match the released upstream script at all three frequencies. The upstream script does not output Average Precision (AP) or ROC-AUC; those columns are produced only by the newly written implementation and are not part of the output-match claim. Upstream stdout evidence is stored in `../gate0_upstream_stdout_capture_20260721/`; current predictions, probabilities, fold manifests, environment metadata and hashes from the new implementation are stored in `../gate0_released_code_rf_all_v2_20260721/`. The earlier `gate0_full_rf_all_20260721` directory is retained but explicitly superseded because the script was parameterised after that run.

## Why the paper table is not yet an exact replication

- The paper text describes depth `4` and minimum leaf size `6`; the released `classifier.py` uses depth `5` and the default leaf size.
- The released feature matrices were added to the repository in November 2021 and include dates through January 2021, whereas the target paper was published in 2020.
- The paper discusses a 104-scheme experiment, while the current matrices contain 327 event groups and 317 groups with at least one positive chunk.
- Running either the released-code parameters or the paper-described parameters on the current matrices does not reproduce every value in Table III.

The cause is therefore not assigned to a single factor. It is recorded as a traceability gap involving at least parameter and data-version differences. The next step is to seek the paper-era dataset/configuration or document that it is unavailable.

## Evidence boundary

This is a single-team local exploratory run, not an independent third-party replication, peer-reviewed result, preprint or publication. It establishes a scoped aggregate-output match for the current public script and exposes a concrete paper-code-data traceability question. It does not establish identical row-level predictions, an end-to-end rebuild of the labels, or replication of the 2020 Table III result.
