# Prompt for external reviewers (Qwen, Z.ai, others)

Copy everything below the line into the reviewer, and attach or link the materials listed under "Materials".
Keep the same prompt for every reviewer so the answers can be compared. Save each reply next to this file
(`qwen-review.md`, `zai-review.md`, ...).

---

You are reviewing a short software-and-typesetting paper and the GitHub repository it describes. I want a critical,
specific review, not an endorsement. Praise is welcome only where you can point to the evidence for it. If you cannot
verify something, say "not verified" and say what you would need to verify it. Do not guess about files you cannot open.

## What the work is

**zitex** typesets Chinese characters with their sound (pinyin), shape and meaning from data, with XeLaTeX and Python.

- A character is a record: its decomposition into parts, the position of each part in an eleven-position notation
  (the Zi-Matrix: L R U D M LU LD RU RD Mi Mo), and a lexicon entry with pinyin, glosses in several languages, and optionally
  a picture.
- Python validates the data and writes one self-contained LaTeX snippet per character and view; a short `.sty`
  only `\input`s them. Views: a one-line formula, an equation with pinyin and glosses, a nested-box matrix, a tree.
- New in this version: `\zimath[pict]{字}` lays an equation out as one grid, per part: pinyin / character / meaning /
  picture, with rows aligned across parts. The picture is an image file, else an emoji (drawn to PNG, because XeLaTeX cannot
  print colour emoji), else nothing. `\zimath[pict=obs]{字}` selects a named set of pictures, here oracle bone glyphs
  from the HUST-OBC dataset.
- Motivation stated in the paper: Chinese characters began as pictographs (oracle bone script shows this), every character has
  sound, shape and meaning, and presenting all three consistently is manual work today.

## Materials

- Paper: `docs/paper/arxiv/main.tex` (PDF: `main.pdf`, same folder).
- Repository: <PASTE GITHUB URL>. Start with `README.md`, `NOTICE`, `docs/DEV/claude/readme-zimath.md` (design of the picture view),
  `docs/GUIDE/TUTORIAL.md`, `examples/pict/` (run `./build.sh`), `src/zitex/`, `tests/test_pict.py`.
- arXiv source: `docs/paper/arxiv/zitex-arxiv-src.tar.gz`.

## What I want you to check

Answer each numbered question under its own heading. For every finding give: a severity (blocker / important / minor),
the exact place (file and line, or section and sentence), what is wrong, and a concrete fix.

1. **Claims against evidence.** List every claim in the abstract and introduction. For each, say whether the paper
   demonstrates it, only asserts it, or contradicts it. Pay attention to "consistently", "not manual work", and
   "a function of the data".
2. **Oracle bone script statements.** Which statements about oracle bone script, pictographs or the glyphs shown (日 月 明
   虫 工 虹) would a specialist in paleography challenge? The paper says it makes no claim about etymology: does the text
   keep to that, including the sentence about 明 and 虹 in the examples?
3. **Related work.** What is missing? Look for LaTeX packages that annotate Chinese text with pinyin or ruby, tools that
   draw character decompositions or stroke order, ideographic description sequence (IDS) resources, and oracle bone databases
   and glyph-evolution sites. Name specific tools or papers, and say what the paper would need to say about each.
   Do not invent references: give a URL or say you are unsure.
4. **Design.** The picture view uses one `array` grid and not stacked `\underbrace` labels; it is a separate opt-in style
   (`pictmath`); pictures are chosen per character from named sets; emoji are rasterised to PNG at build time. Are these good
   decisions? What would break, and for whom (Overleaf, MathJax users, other engines, long equations, right-to-left text)?
5. **Reproducibility.** From the repository alone, can a reader rebuild the figures in section 4? Try
   `examples/pict/build.sh` and `./make-arxiv.sh` in `docs/paper/arxiv` if you can run code, otherwise read them. List
   hidden dependencies (fonts, Python version, Inkscape, Pillow, a database not in the repository).
6. **Licensing and data.** The code is MIT. The glyph images are CC BY-NC 4.0 (HUST-OBC), the glosses derive from CC-CEDICT
   (CC BY-SA 4.0), and a font subset is under the SIL OFL. Is the repository's `NOTICE` correct and sufficient? Is
   it acceptable to put CC BY-NC images in a repository whose code is MIT, and to bundle a font subset in an arXiv source?
7. **Code quality.** Read `src/zitex/lexicon.py`, `render.py` (`render_pictmath`), `build.py` and `zitex.sty`. Report bugs,
   places where `zitex.sty` and the Python side could disagree (snippet names such as `u660e-pictmath-obs-zh.tex`), missing
   tests, and error handling that fails silently.
8. **Writing.** Where is the paper unclear, repetitive, over-claiming or too long for what it shows? Mark the three sentences
   you would cut first, and the one question a sceptical reader would ask that the paper does not answer.
9. **arXiv readiness.** The paper must compile with XeLaTeX (`00README.json` selects it) and carries a subset of Noto Serif
   CJK SC. What could make the arXiv build fail or look different from the local PDF? Which arXiv subject class fits (cs.CL, cs.DL, cs.HC, other),
   and why?

## Known limits (do not report these as discoveries)

- XeLaTeX only; the picture view is not available in MathJax.
- A long equation with long meanings can overflow the page; there is no automatic scaling.
- Only a handful of oracle bone glyphs have been chosen by hand so far (53 of the 306 elemental characters that have one).
- The related-work section does not compare with other tools; the paper says so.
- Six tests in `tests/test_pipeline.py` and `tests/test_ui.py` fail on the author's machine and are not caused by the picture view.
- The decomposition database used for development is not in the repository in full.

## Output format

1. A verdict in three sentences: what the work contributes, whether it is ready for arXiv, and the single most important fix.
2. Findings for questions 1 to 9, ranked inside each question by severity.
3. A short list titled "Not verified": things you could not check and what would settle them.

Be direct. If the paper is not ready, say so and say why.
