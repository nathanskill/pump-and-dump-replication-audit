# ANONYMIZATION_NOTES — REF-2026-016 LaTeX project (FC 2027 submission)

Source of truth: `paper/manuscript_draft_v0.5.md` (2 Aug 2026). This file
records every difference between the **anonymized build** and the **named
build** of `main.tex`, plus the format adaptations applied to both builds, so
that nothing from the markdown source is lost.

## Build toggle

One source file, two builds. In `main.tex` (top of file):

| Toggle | Anonymized build (default) | Named build |
|---|---|---|
| `\anonymoustrue` / `\anonymousfalse` | `\anonymoustrue` | `\anonymousfalse` |
| `\neutralpositionalitytrue` / `...false` | default `false` (see item C below) | `false` |

## Venue requirement (checked 1 Aug 2026)

FC 2027 CFP (https://fc27.ifca.ai/cfp.html): research papers "must be
anonymized with no author names, affiliations, acknowledgments, or obvious
references" — improper anonymization is grounds for desk rejection. The CFP
explicitly permits the paper to exist online in non-anonymous form (e.g.
preprint/repository), and PC members are instructed not to seek to
de-anonymize.

## A. Redactions active in the anonymized build

1. **Author block (title page).**
   - Named: `Zhennan Yu`, `Independent Researcher, Sydney, Australia`,
     `yuzhennan323@gmail.com` (byline per manuscript header "Zhennan (Nathan)
     Yu — Independent Researcher, Sydney, Australia"; confirm preferred name
     form and email before the named build is used).
   - Anonymized: author `Anonymous Submission to FC 2027`, no institute, no
     email. Running head likewise.

2. **Repository link, Sect. 8 (Reproducibility Statement), first sentence.**
   - Named: `github.com/nathanskill/pump-and-dump-replication-audit`
   - Anonymized: `[link redacted for review; artifacts available to reviewers
     on request]`
   - Implemented as the `\repolink` macro; this is the only place in the
     manuscript where the repository URL appears.

## B. Warnings for the anonymized build (manual, cannot be automated)

- **Zenodo DOI placeholder (Sect. 8, Data availability).** Both builds keep
  the literal placeholder *[Zenodo DOI to be inserted at preprint.]*. Do NOT
  insert a real Zenodo DOI into the anonymized build: the Zenodo record names
  the author. Insert it only in the named/preprint build.
- **Submission-site metadata** (author names, COI declarations against PC
  members) is entered on the FC submission site, not in the PDF.

## C. Conditional neutralization (default OFF): positionality sentences

The FC 2027 CFP bans author names, affiliations, acknowledgments and obvious
references; it does not clearly require removing non-identifying positionality
detail, and "the author" phrasing is standard in double-blind submissions. The
two clauses below are therefore KEPT by default in the anonymized build, but a
one-line toggle (`\neutralpositionalitytrue`) neutralizes them if, at
submission time, the chairs' guidance or reviewer-facing checklists ask for it.

3. **Sect. 5.2 (The 5-Second Degradation).**
   - Full text (default, both builds): "Beyond the mechanics, the author's
     reading — from several years working in the retail-trading industry,
     where coordinated promotional campaigns are observed operationally — is
     that a pump is a burst produced by a coordinated group, ..."
   - Neutralized (toggle on): "Beyond the mechanics, the author's reading is
     that a pump is a burst produced by a coordinated group, ..."
   - Nothing is lost: the removed clause is exactly "— from several years
     working in the retail-trading industry, where coordinated promotional
     campaigns are observed operationally —".

4. **Sect. 5.3 (Practitioners paragraph).**
   - Full text (default, both builds): "Second, in the author's experience of
     promotion channels, much of the visible 'community' ..."
   - Neutralized (toggle on): "Second, in the author's assessment of promotion
     channels, ..." (single word `experience` → `assessment`).

## D. Reviewed and intentionally NOT redacted

- "the author" phrasing throughout Sect. 5 (standard anonymous phrasing).
- Sect. 2 inquiry sentence: "sent to the corresponding author on 22 July
  2026" refers to the *upstream paper's* corresponding author (La Morgia et
  al.), not to this paper's author.
- AI-assistance disclosure (Anthropic Claude): tool disclosure, not identity.
- Abstract's final sentence "Code, protocols and hash-verified aggregate
  artifacts are public": the FC CFP explicitly allows non-anonymous online
  availability; the sentence contains no link (the link itself is redacted,
  item A2).
- Commit hashes `c2736ed`, `23089ce`, `d71250d`, artifact directory names,
  and the release tag `v0.2.0-results-freeze`: not searchable to an identity
  without the (redacted) repository URL.

## E. Format adaptations applied to BOTH builds (markdown → LNCS)

None of these change scientific content; listed so nothing is silently lost.

1. **Draft banner removed.** The v0.5 line "*DRAFT v0.5 — 2 August 2026
   (related-work additions for venue submission). Not submitted, not peer
   reviewed. All quantitative results were produced under the protocol frozen
   at repository commit `c2736ed` (amendments A1–A3; see Section 8 on commit
   identifiers).*" is draft metadata; the protocol-freeze fact it states is
   retained verbatim in Sect. 8.
2. **"Figures" list section dissolved into real floats.** The two figure
   descriptions became the captions of Fig. 1 and Fig. 2. The section's
   parenthetical regeneration note is preserved as the final sentence of each
   caption ("Generated by `src/make_figures.py` from the per-row prediction
   artifacts, which are not redistributed; see the Data Availability
   statement."); the now-obsolete phrase "to be typeset at preprint" was
   dropped. Vector PDFs (`figures/fig1_pr_curves.pdf`,
   `figures/fig2_checkpoints.pdf`) are used; the PNGs are kept alongside as
   fallback.
3. **Keywords added** (`\keywords{...}`): the markdown has none, LNCS requires
   them — author to confirm/adjust.
4. **Table lead-ins.** Markdown tables introduced by a trailing colon now get
   explicit `Table~\ref{...}` references (floats can drift); Table 4.3's long
   header parenthetical and the italic S0-refit note were folded into that
   table's caption; Table 4.1's asterisk footnote lives in its caption. All
   numeric cell values are verbatim, including the deliberate leading-dot
   style (".9479") of the checkpoint table.
5. **Citation numbering preserved.** `\bibitem` order matches the markdown's
   1–28 exactly, with the markdown's exact metadata; the `cite` package
   compresses ranges (e.g. [7–10]). `splncs04.bst` is included only for a
   possible later switch to BibTeX.
6. **Inline status placeholders kept verbatim** as bracketed italics:
   Sect. 2 *[STATUS AT SUBMISSION: pending — resolves 5 August 2026 ...]*,
   Sect. 8 *[Zenodo DOI to be inserted at preprint.]* and *[Adapt to venue
   disclosure format at submission.]*. Resolve all three before submission.

## Pre-submission checklist

- [ ] Resolve Sect. 2 upstream-inquiry status line (5 Aug 2026 rule).
- [ ] Decide `\neutralpositionality` toggle against final FC 2027 guidance.
- [ ] Confirm keywords.
- [ ] Verify `\anonymoustrue` is set; search the PDF for "Yu", "nathanskill",
      "Sydney", the email, and the Zenodo DOI before upload.
- [ ] Check page budget: FC 2027 regular papers = 15 pages + references and
      appendices.
