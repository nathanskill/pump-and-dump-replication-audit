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

---

## 2026-08-04 — verification pass and two changes

Verified by resolving the `\ifanonymous` conditional line-by-line in both
directions and scanning each emitted build. Environments balance in both;
all 28 `\cite` keys resolve against 28 `\bibitem`s with no unused entries;
both `\includegraphics` targets exist as PDF.

**Anonymous build: clean.** No author name, no `github.com`/`nathanskill`,
no archive name, no DOI, no employer, no affiliation string, no email
address, no acknowledgements section.

**Named build: leaks exactly what it should** — author (L79, L82),
repository (L56), affiliation (L81), email (L82), archive name (L705).

### Change 1 — stale release tag

The Data-availability paragraph named `v0.2.0-results-freeze`. That is not
the archival target. On 2026-08-02 the `CITATION.cff` version error was
fixed by cutting `v0.2.1-results-freeze` rather than force-moving the
published `v0.2.0` tag; the fix was applied to `CITATION.cff` alone, and
three places that a reader acts on were left pointing at the old tag
(`README.md`, the Markdown manuscript draft, and this LaTeX source).
Releasing from `v0.2.0` would make the archive read the superseded
`CITATION.cff` and mint the record as `v0.1.0-protocol-freeze`, reinstating
the exact defect `v0.2.1` exists to avoid. All three now name `v0.2.1`.

### Change 2 — archive name is now conditional

Previously both builds read "archived under a persistent DOI (Zenodo)"
followed by the placeholder "Zenodo DOI to be inserted at preprint."

The FC 2027 CFP expressly permits non-anonymous preprints ("It is
acceptable ... for submitted papers to be published online in non-anonymous
form"), so naming the platform would **not** have breached the call. But the
deposit record names the author, and the record will be public before the
submission deadline. Naming the archive hands a reviewer a one-search
lookup for no benefit. The anonymous build now reads "Archive DOI withheld
for anonymous review"; the named build is unchanged.

### Open blocker, not an anonymisation issue

**There is no TeX toolchain on this machine** — no `pdflatex`, `xelatex`,
`latexmk` or `tectonic`, and no Homebrew to install one. FC requires a PDF.
The build has therefore never been executed and the true page count is
unknown; the estimate is ~10.3 pages of prose plus two figures, tables and
references, against a 15-page limit (plus references and appendix) for a
regular submission. Resolve this well before 17 September rather than on
the day: either install BasicTeX/MacTeX, or upload `main.tex`, `llncs.cls`,
`splncs04.bst` and `figures/` to Overleaf, which needs no local install.

---

## 2026-08-09 — pre-submission checklist closed out

The open blocker recorded on 2026-08-04 ("no TeX toolchain on this machine")
is resolved: the project was compiled on Overleaf (TeX Live 2025, pdfLaTeX).
**13 pages, 0 errors.** The FC limit is 15 pages *excluding* references and
appendices; the body runs to mid-page 11, references to mid-page 13, and
Appendix A sits on page 13 — so the real headroom is about four body pages,
not two. The page-count worry that ran through this file was unfounded.

### Checklist, resolved

- [x] **Sect. 2 upstream-inquiry status line.** Resolved 5 Aug 2026 under the
      pre-declared Scenario A rule (no reply received); the placeholder is
      replaced by the declared text.
- [x] **`\neutralpositionality` toggle: stays FALSE.** The two positionality
      clauses are kept in the anonymous build. The CFP bans "author names,
      affiliations, acknowledgments, or obvious references"; "several years
      working in the retail-trading industry" is none of those, names no
      employer, and does not narrow the author to a findable person. It is
      also load-bearing — it is the paper's only statement of why the author
      reads the 5 s degradation the way Sect. 5.2 reads it. Neutralising it
      would cost an argument to buy no anonymity.
- [x] **Keywords confirmed** as they stand.
- [x] **`\anonymoustrue` verified**, and the compiled PDF — not the source —
      was scanned page by page with pypdf for "Yu", "Zhennan", "Nathan",
      "nathanskill", "Sydney", the email, "zenodo", "10.5281" and
      "Independent Researcher". All absent. The one `github` hit is
      reference [2], the upstream artifact being audited, which must be
      cited. Document-info metadata carries no author string.
- [x] **Page budget** checked against the correct ruler (above).

### Item E6 was not fully discharged, and this is the correction

E6 listed three bracketed placeholders to resolve before submission. Two were
resolved on 2026-08-04. The third — *[Adapt to venue disclosure format at
submission.]*, trailing the AI-assistance disclosure — was missed, and it
survived into the compiled PDF on page 11. It was caught on 2026-08-09 by a
scan for bracketed text in the extracted PDF, i.e. by looking at the artifact
rather than at the source.

It is now removed. FC 2027 prescribes no wording for AI-assistance
disclosure, so the paragraph stands as written and the instruction is
discharged; a comment in `main.tex` records that, so the note cannot read as
an oversight later.

**Lesson worth keeping:** the earlier verification pass resolved the
`\ifanonymous` conditional by hand and scanned the *source*. That method
cannot see a placeholder in unconditional prose. Scan the compiled PDF.

### Named build was broken and is now fixed

The named build could never have compiled: the Data-availability paragraph
used `\href` while the project loads neither `hyperref` nor anything that
defines it. Only the anonymous branch had ever been built, so the defect was
invisible. `\href` is replaced by `\url` (the `url` package is already
loaded), which prints the same address without pulling `hyperref` in late and
disturbing LNCS float placement.

### Camera-ready obligations, recorded now so they are not improvised in December

Due 22 December 2026 (final pre-proceedings; the Springer camera-ready is a
separate, later deadline):

1. **Springer requires a third-level "Disclosure of Interests" heading in
   9 pt beneath the acknowledgments, even when there is nothing to declare.**
   It is absent, correctly, from the anonymous build.
2. That statement should name the retail-FX/CFD employment and state that no
   employer data or resources were used. Not naming it is defensible — the
   FC ethics page triggers on an organisation that "may gain or lose
   financially through this publication", which a broker does not, from a
   replication of a public Bitcoin pump-and-dump classifier — but Sect. 5.2
   already invokes industry experience as grounds for a reading, so silence
   in the disclosure would sit worse than the sentence itself.
3. Reference list is ordered neither by first citation nor alphabetically.
   `splncs04.bst` is in the project; the entries are inline `\bibitem`s, so
   fixing it means converting to a `.bib` or renumbering by first citation.
4. Alt text for Figs. 1–2 and Tables 1–6.
5. Fig. 2's three frequency series are distinguished by colour alone; give
   them distinct markers or dash patterns so they survive greyscale print.
6. The author list and corresponding author freeze at camera-ready.
7. If accepted, tell the chairs in one line that the Zenodo deposit already
   exists — the IFCA copyright form's retained right 4 asks authors to inform
   IFCA of pre-publication distribution. The CFP's explicit blessing of
   non-anonymous preprints is the operative permission, so this is courtesy,
   not a cure for a breach.
