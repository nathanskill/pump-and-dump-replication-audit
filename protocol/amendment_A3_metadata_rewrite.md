# Amendment A3 — commit-metadata rewrite (author identity; AI-assistance trailer removal)

Date: 2026-07-23 (Australia/Sydney)

## What changed and why

All nine commits prior to this amendment were authored with a machine-local
email address (`zhennan@…local`) that does not map to any GitHub account, and
carried an AI-assistant `Co-Authored-By` trailer in the commit message. The
commit chain was rewritten with (a) the author's real identity — Zhennan Yu
<yuzhennan323@gmail.com> — and (b) the trailers removed. Formal disclosure of
AI assistance in this project is made in the manuscript acknowledgements, not
in git metadata.

## What did NOT change

Every rewritten commit reuses the original tree object unchanged: file
contents, author dates, committer dates, and commit order are identical
commit-for-commit. This was verified by comparing the tree-hash sequences of
the old and new chains (`git log --format=%T`), which are equal.

Historical protocol documents (amendments A1/A2, the frozen CV/ablation spec)
and recorded run artifacts (`artifacts/*`) keep their original in-text
references to the old freeze SHA; the mapping below is authoritative for
resolving them. Operational references (README, `src/run_formal_cv.py`,
`src/run_formal_forward.py`) are updated to the new SHA in the same commit
that adds this amendment.

## Freeze-commit re-anchor

Protocol v0.2 freeze commit: `23089ce` → `c2736ed`
(`23089ceebd93eed421b8a2a710135851dcab536e` →
`c2736ed36e6a074ded78e916c071d5d396b316c3`).
The annotated tag `v0.1.0-protocol-freeze` now points at the rewritten freeze
commit.

## Full old → new SHA map

```
9d1d755f38a703a92ded954d5a014dc3f4667983 -> 1392566f5139efadd7df0a609001604fe803d692  initial public release
23089ceebd93eed421b8a2a710135851dcab536e -> c2736ed36e6a074ded78e916c071d5d396b316c3  protocol v0.2 freeze
d52f8ae57905da09598faff4368a98096c348a97 -> 9a8cf73b7b318b52161d1eb953a2167502dcaa6e  amendment A1
de6372d5505ba834be7d81116ce3936fae4b4184 -> a491559649e5f484c986319c76960bcc3f0667a7  formal S2 forward runs
f13f310674b49818e889a22cb73932b0fd5c9b2b -> b4cfd2628c3923979799997181b7083fe35a5537  freeze S1/S0 + ablation spec
2aa491bfbc90aa4883d752f1058e314413415583 -> 3d46af47d95edd46adca6947723c4ef7ebf31720  formal S1/S0 + ablation results
72a3896ab9b670ebba7a00174de0b70c056aace5 -> 242f4b07ed457f6ddc97d8b4a3a8f28df67d9784  amendment A2
85d87251e83ef2e2a73e57be65c1ce06bf0ddb0b -> 0852c4ea73339461c82ce20fdb2e7508c6502c92  manuscript PDF renderer
dc221a24f398c4c107206225e14b2ae5decb9805 -> bd2913088372ce6cefddf046e69dc91a6409d368  README results summary
```
