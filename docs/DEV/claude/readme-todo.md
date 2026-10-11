# zitex: to do

Written 2026-10-11. State: `main` is pushed to GitHub. The arXiv source is `docs/paper/arxiv/zitex-arxiv-src.tar.gz`
(8 pages, compiles clean); the abstract for the form is `docs/paper/arxiv/zitex-arxiv-abstract.txt` (ASCII).
Not submitted yet.

## 1. Publish to PyPI (from another machine; this one has no token)

PyPI already has `zitex` 0.1.0 and 0.2.0, and `pyproject.toml` here still says 0.1.0. A version cannot be uploaded twice,
so the release needs a new number above 0.2.0 (for example 0.3.0).

1. Pull `main`.
2. Set the version in `pyproject.toml` and in the fallback in `src/zitex/__init__.py`.
3. `pip install build twine`, then `python -m build`.
4. Optional check in a clean environment: `pip install dist/*.whl && zitex --help`.
5. `twine upload dist/*`, with username `__token__` and the API token as the password. Keep the token out of any repo folder
   (`~/.pypirc`, or `TWINE_USERNAME` / `TWINE_PASSWORD` in the shell).

The `pyproject.toml` `Paper` URL still points to the earlier model paper (arXiv:2502.19428). Change it to this paper once it
has an arXiv number.

## 2. Before submitting the paper to arXiv

Author:
- Proofread `zitex-arxiv.pdf`. Section 4 is the part to check (what the glyphs show, and what the equations do not claim).
- Read the related work the reviewers named and add what you confirm (one sentence each): Make Me a Hanzi, Hanzi Writer,
  CUHK Multi-function Chinese Character Database, cjk-decomp, BabelStone IDS, Richard Sears's hanziyuan, Xiaoxuetang,
  CHISE, GlyphWiki, Unihan, `ruby` / `pxrubrica`, `mhchem` / `chemfig`, and the Unicode 15.1 IDS operators. None was
  verified by Claude. The notes are in `docs/paper/feedback/take-by-claude.md` (section 7, item 9).
- Choose the licence at the arXiv form. The glyph figures are CC BY-NC, so not CC BY or CC BY-SA: arXiv's default
  non-exclusive licence, or CC BY-NC-SA. arXiv's current menu was not checked.
- Optional: have a paleographer read section 4 (not a blocker).
- Check the HUST-OBC bibliography entry; a Scientific Data DOI was suggested by a reviewer and is not verified.

Upload (steps, in order):
1. New submission, upload `zitex-arxiv-src.tar.gz`.
2. Check that arXiv picks XeLaTeX from `00README.json` (key `process.compiler`); set it by hand if not.
3. Compare arXiv's preview PDF with the local `zitex-arxiv.pdf` (fonts, picture rows, Chinese text). This also settles
   TeX Live 2025 and the `sources` key, which were not tested.
4. Category: physics.soc-ph primary (the author's earlier paper is there); optional cross-list cs.CL or cs.DL. Moderators
   may reassign it.
5. Paste the title and `zitex-arxiv-abstract.txt` into the form.

Rebuild before uploading if the text changed: `docs/paper/arxiv/make-arxiv.sh` (regenerates the snippets with `--strict`,
the font subset, the tarball, and compiles it in a clean folder). It does not update `zitex-arxiv.pdf`; compile that
with `xelatex zitex-arxiv.tex`, twice (do not set `TEXINPUTS=.` without a trailing colon: it hides the system TeX tree).

## 3. Code and packaging, not done

From the Opus review (`docs/paper/feedback/take-by-claude.md`, section 7):
- Record the emoji font name and version in `build_manifest.json`; pin the Noto version in `docs/paper/arxiv/fonts/README.txt`.
- Replace the regex scanner (`scan_tex`) by a job file the package writes (`\jobname.zitex`), so scanner and package cannot
  disagree, and macros that wrap `\zimath` work. Larger change.
- A web (HTML) form of the picture view (KaTeX and MathJax cannot show it).
- The committed arXiv tarball can go stale: build it in CI or remove it from git.
- `db/NOTICE.md` should also list `zitex-orig.sqlite3` and the `review-*.csv` files.
- The glyph-selection script lives in Orascope (`scripts/export_picts.py`); publish it or describe the selection in the paper.
- A requirements list with versions, a CI job that builds `examples/pict` and the arXiv tarball in a clean container,
  and a compatibility table (XeLaTeX, pdfLaTeX, LuaLaTeX, MathJax, Overleaf) in the README.
- Not tested: macOS and Windows (emoji font paths), Overleaf, LuaLaTeX, Python other than 3.13 (3.10 is declared).
- `zx_meta.quarantined` says 223 but `zx_quarantine` has 222 rows (a revision re-applied during the build); the paper says "about 220".

## 4. Tests

With `PYTHONPATH=src pytest`, 361 pass and 7 fail, all in `tests/test_ui.py`. The cause is Streamlit 1.32.2 on this machine
rejecting `width="stretch"` in `st.data_editor`; the `ui` extra asks for Streamlit 1.50 or newer. The pipeline tests need
`zitex` importable (`pip install -e .` or `PYTHONPATH=src`), because they run `python -m zitex` in a subprocess.

## 5. Later, only if the paper grows

- A timed comparison with hand-made figures, or a user study.
- A larger handout (30 to 50 equations) from the database as a teaching example (`benchmarks/handout.py` is the start).
- A calligraphy picture set and more chosen glyphs (use `scripts/export_picts.py` in Orascope).
