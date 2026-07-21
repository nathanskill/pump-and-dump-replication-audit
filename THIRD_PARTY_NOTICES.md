# Third-Party Notices

## Upstream dataset and reference implementation

- Repository: [SystemsLab-Sapienza/pump-and-dump-dataset](https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset)
- Pinned commit used by this study: `d71250d4cb055dde2d415c8cba38a0dcd6eb6e16`
- Associated paper: M. La Morgia, A. Mei, F. Sassi, J. Stefa, *Pump and Dumps in the Bitcoin Era: Real Time Detection of Cryptocurrency Market Manipulations*, ICCCN 2020, DOI `10.1109/ICCCN49398.2020.9209660`.
- Upstream licence: MIT, copyright `2020 SystemsLab-Sapienza` (licence file SHA-256 `e81234099e71b667dae61b2580d49b7bd567d61492f909fd376bc2cca1e2a858`).

The upstream MIT licence permits use, modification and redistribution of the software and associated documentation subject to preservation of the copyright notice. It does not separately identify the licence status of every data file or underlying exchange transaction record. Pending clarification of the data boundary with the original authors and the target venue, this repository:

- does not re-upload the upstream labelled feature matrices, raw transaction records, Telegram group list, or event file;
- records upstream input filenames, SHA-256 hashes, the pinned commit, and acquisition instructions instead;
- contains no code copied from the upstream repository — `src/` is a newly written implementation compared against the upstream script's outputs.

Reference file hashes from the source audit (`protocol/source_and_licence_audit_v0.1.md`):

| Upstream file | SHA-256 |
|---|---|
| `LICENSE` | `e81234099e71b667dae61b2580d49b7bd567d61492f909fd376bc2cca1e2a858` |
| `README.md` | `ca761629e7ea2305b56741816b74b87fdb0436f1796599b743394e92131ba39a` |
| `features.py` | `b02c14034f837bc625cb9df6baff7046d2186fb5f32cb5da056b8acaeedd083f` |
| `classifier.py` | `05e130af9cf1431ee6de417bbeece3822303e1ba6b62cb352d26699ec265ddde` |
