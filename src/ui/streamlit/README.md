# zitex Streamlit app

Two pages: review the decompositions in the database, and generate `main.pdf` for a list of characters.

```bash
pip install -e ".[ui]"                       # once: streamlit (1.50 or newer) and pandas
streamlit run src/ui/streamlit/app.py        # from the repository root, or give the full path
```

It needs a zitex database made by `zitex db-build` (the default is `db/zitex.sqlite3`, found like `zitex extract` finds it),
and, for the pictures and the PDF, `xelatex` and `pdftoppm` (poppler).

## Page 1: Review decompositions

- **Look up** a character: pinyin, meaning, the shape string, its pattern, warnings, notes, and a picture (matrix or tree).
  It also shows how many other characters use it as a part.
- **Revise** it: an editable table of (position, part), one row per part. Delete all the rows to make the character a
  primitive. **Check the change** tries it on a throw-away copy and shows the new shape and any warnings; **Save revision**
  writes it. Tick *elemental* to say the character is never expanded inside others (as for 弗, kept whole in 佛).
- **Revert to the original** puts back what the database had.
- **What to review** lists the work: rows left out of the database, elemental characters that still have a decomposition,
  patterns that use `Mi`, a radical labelled `M` (W8), overlapping regions (W7), and your own revisions. Select a row to open it.
- **Revisions** can be downloaded as CSV, to apply them to your working database.

Revisions are saved in the zitex file (table `zx_revision`) and survive `zitex db-build`. Your working database is never
opened for writing.

## Page 2: Generate main.pdf

Type or paste characters (commas or spaces; at most 60). **Generate main.pdf** runs, in `workspace/`:

```bash
zitex setup -o workspace
zitex extract -i <database> -c <characters> -o workspace
cd workspace && xelatex main.tex
```

and shows the pages, with a download button, the output of each step, `main.tex` and `chars.yaml`.
`workspace/` is generated and is ignored by git.

## Layout

```
src/ui/streamlit/
  app.py                          home: what the app does, and what is installed
  common.py                       the sidebar database box, paths, tool checks
  pages/1_Review_decompositions.py
  pages/2_Generate_main_pdf.py
```

The logic lives in the zitex package (`zitex.review`, `zitex.pipeline`, `zitex.zxdb`), so it is tested without a browser;
`tests/test_ui.py` runs the pages headless with Streamlit's test harness. This folder has no `__init__.py` on purpose: a package
named `streamlit` would hide the real one.
