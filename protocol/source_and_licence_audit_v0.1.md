# REF-2026-016 Source and Licence Audit v0.1

> Status: `PARTIAL / REDISTRIBUTION BOUNDARY PENDING`  
> Date: 2026-07-21

## Upstream source

- Repository: `https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset`
- Pinned local commit: `d71250d4cb055dde2d415c8cba38a0dcd6eb6e16`
- Associated paper: La Morgia et al., *Pump and Dumps in the Bitcoin Era: Real Time Detection of Cryptocurrency Market Manipulations*, ICCCN 2020, DOI `10.1109/ICCCN49398.2020.9209660`.

## Repository licence

The repository root contains an MIT licence with copyright `2020 SystemsLab-Sapienza`.

- `LICENSE` SHA-256: `e81234099e71b667dae61b2580d49b7bd567d61492f909fd376bc2cca1e2a858`
- `README.md` SHA-256: `ca761629e7ea2305b56741816b74b87fdb0436f1796599b743394e92131ba39a`
- `features.py` SHA-256: `b02c14034f837bc625cb9df6baff7046d2186fb5f32cb5da056b8acaeedd083f`
- `classifier.py` SHA-256: `05e130af9cf1431ee6de417bbeece3822303e1ba6b62cb352d26699ec265ddde`

The MIT text clearly permits use, modification and redistribution of the software and associated documentation subject to preservation of the notice. It does not separately identify the licence status of every data file or underlying Binance transaction record.

## Safe release boundary pending author/venue clarification

Until the data boundary is clarified, the REF-2026-016 public release will:

- publish Nathan's newly written source code and tests under a chosen compatible code licence;
- cite the upstream paper and repository;
- record input filenames, hashes, commit and acquisition instructions;
- publish split manifests, configurations, aggregate metrics and figures;
- avoid repackaging or re-uploading the upstream labelled feature matrices, raw transactions, Telegram group list or event file;
- require users to acquire upstream inputs from the original source.

This conservative boundary is a research-release choice, not a legal conclusion. Gate 0 remains open until the target venue requirements and, if needed, the original authors clarify data redistribution and reuse expectations.

## Remaining actions

1. Check the paper and repository history for any explicit dataset terms beyond the root MIT licence;
2. check Binance historical-data terms only if building the optional natural-background stream;
3. prepare a concise author query covering exact reproduction details and whether derived manifests/aggregates may be released;
4. preserve all upstream notices in `THIRD_PARTY_NOTICES` before candidate release.

