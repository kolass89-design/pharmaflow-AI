# MYP 5 eAssessment — Worked Answer Sheet

**Deliverable:** `MYP5-eAssessment-Answer-Sheet.pdf` — 54 pages, A4, print-ready.

A complete worked-solution and marking guide for every task in the 56-page
*MYP 5 Mathematics eAssessment-style question bank* (Criteria B, C and D):

* 43 tasks · 537 marks · one block per task part
* worked method → boxed final answer → mark allocation → examiner note
* section openers, contents page with page numbers, PDF bookmarks for every task
* appendices: how marks are awarded, criterion coverage, formula bank,
  ten exam habits, and an answer key at a glance

## Rebuilding the PDF

```bash
pip install reportlab fonttools
python3 build.py          # writes MYP5-eAssessment-Answer-Sheet.pdf (two-pass, so the
                          # contents page can show real page numbers)
```

| File | Purpose |
| --- | --- |
| `build.py` | layout engine (ReportLab platypus): cover, section dividers, task tables, pages/decorations |
| `content_bcd.py` | solutions for Sections 2–4 (Criteria B, C, D) |
| `content_rest.py` | solutions for Sections 5–13 plus the appendices |
| `marks_from_paper.py` | marks per part, extracted from the question bank and checked against each task total |
| `fonts/` | Open Sans and Source Serif 4 (SIL OFL 1.1) — the PDF embeds subsets, so the fonts are only needed to rebuild |

Mathematical notation is real text: `<super>`/`<sub>` markup plus a DejaVu Sans
fallback for the handful of glyphs Open Sans lacks (→ ∠ ⊥ ✓). The build fails
loudly if a task's part marks do not add up to the printed total.

## Notes on the question bank

Two internal inconsistencies in the source paper are handled explicitly in the
solutions rather than hidden:

* **P1** — the printed tree diagram (3/5, 2/5, 1/2, 3/4) does not match a bag of
  5 red and 4 blue marbles; the correct tree (5/9, 4/9 then 4/8, 5/8) is given
  and the discrepancy is flagged.
* **D8** — the plotted line is `y = 2.9x + 7.0` while part (d) quotes a gradient
  of 3.2; both readings are accepted and the interpretation is what is marked.
