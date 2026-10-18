# zitex

Chinese character decompositions as typeset equations, trees and diagrams, through XeLaTeX.

Write what a character is made of, once, in YAML:

```yaml
- char: 時
  pinyin: shí
  meaning: time
  shape: "⿰日寺"
```

A character has three dimensions: **sound** (音, `pinyin`), **meaning** (義, `meaning`, or glosses in any language) and **shape** (形). The `shape` field holds how the character is built, a decomposition in Unicode's Ideographic Description Sequence notation (plus ZiNets operators for flat patterns). A *picture* of the glyph, an oracle bone glyph, a small image or an emoji, is a separate optional `pict`. zitex typesets them together, as a reaction-style equation with pinyin above and a gloss below each piece:

```
 rì     sì          shí
 日  +  寺   ──→   時
 sun   temple       time
```

and, with the picture row (`\zimath[pict]{明}`), as a grid in which every part carries its sound, its meaning and its shape:

```
 rì      yuè      míng
 日   +   月   =   明
 sun     moon     bright
 ☀       🌙       ✨          (the real output has pictures: emoji, or oracle bone glyphs with pict=obs)
```

(See `examples/pict/` for the picture view, `examples/m2/equations.pdf` for the other styles, and `examples/demo/` for a complete paper.)

zitex is part of the **ZiNets** project. It turns the paper's ideas into something you can put in your own documents: the 422 **elemental characters** (元字), the **Zi-Matrix** with its eleven spatial positions (上 下 左 右 中 左上 右上 左下 右下 中内 中外), and character families that build on one another.

## Background

The model comes from:

> Wen G. Gong. *A New Exploration into Chinese Characters: from Simplification to Deeper Understanding.* arXiv:2502.19428, February 2025. https://arxiv.org/abs/2502.19428

The paper analyses over 6,000 characters, identifies 422 elemental characters as building blocks, and describes character structure across eleven spatial positions. `zitex` is a tool for writing and typesetting decompositions in that model. It is not an implementation of the paper's analysis, and it does not ship the 422-character data.

An early sketch of a LaTeX package for this lives in `docs/DEV/gemini/readme.md`. It was a useful starting point, but it had problems: an 11-argument macro that was hard to use, an undefined command, a wrong decomposition of 藻, and enclosures drawn as grid cells when they are relations. zitex replaces it with a small Python layer that does the parsing and layout, plus a thin LaTeX package.

## What it does

| Style | Output |
|---|---|
| `math` | an equation: `女 + 子 = 好`, pinyin above, gloss below each piece, in the language you choose |
| `formula` | one line: `日 + 寺 → 時 (shí, time)` |
| `tree` | a decomposition tree, with the position on each edge |
| `matrix` | nested boxes laid out by operator: the Zi-Matrix |
| `pictmath` | the equation as one grid: pinyin / character / meaning / picture, rows aligned across the parts (`\zimath[pict]`; opt-in) |

- **Compact input.** A `shape` string, such as `⿱艹⿰氵喿(⿱品(∴口口口)木)` for 藻, or explicit YAML trees with a position on every component.
- **The Zi-Matrix positions.** Eleven position codes (`L R M U D Mi Mo LU LD RU RD`), where `M` is the center of gravity and a Kangxi radical is peripheral, so 佛 is 亻(`L`) + 弗(`M`).
- **ZiNets operators for flat patterns.** `∴` (品, 叒), `∵` (哭), `∷` (叕), `⁙` (器: four 口 around 犬) and a general `<pattern>` form keep a level with three or more parts as one level, which standard IDS cannot.
- **A picture row (`pict`).** Under each meaning goes a picture: an image file, else an emoji (drawn to PNG, because XeLaTeX cannot print colour emoji), else nothing. Every picture is set in a box of the same size, set in a `.env` file (`.env.example`). Pictures come in **named sets**: `\zimath[pict=obs]{字}` uses the lexicon key `pict_obs`, so one document can show the same equations with emoji and with oracle bone glyphs from [HUST-OBC](https://github.com/Pengjie-W/HUST-OBC).
- **What goes under a character.** Its gloss, else its `concept` (ALL CAPS, such as `HAND`), else its `category` (`HUMAN-BODY`), else nothing. Concept and category come from the Orascope project.
- **Chemistry-style extras.** Repeats collapse (`3 × 木 = 森`), and the arrow can carry the reason for the combination (`忄 + 每 —(sound: měi)→ 悔`).
- **Two data sources.** A hand-written `chars.yaml`, or the ZiNets SQLite database (6,000 characters), through the same commands. The database is read only and never changed.
- **Several languages.** Glosses come from a lexicon file and fall back to English.
- **Several readings.** A character can carry competing interpretations of its parts (for example the dictionary's and the author's), and you pick one when rendering.
- **Fonts that fall short.** Fallback fonts, SVG images for components with no code point, and a coverage report.
- **Two outputs.** `.tex` snippets to `\input` into a paper, and compiled PDF figures.
- **Web-ready.** The `math` output uses only commands that MathJax and KaTeX also understand.

## Install

```bash
pip install zitex         # from PyPI: Python 3.10+, installs the `zitex` command
pip install -e .          # or from a checkout, to work on the code
```

You also need XeLaTeX with `tikz`, `xeCJK` (on Debian or Ubuntu: `texlive-xetex`, `texlive-lang-chinese`, `texlive-pictures`), `fontspec`, `amsmath` and `graphicx`, and a CJK font (Noto Serif CJK SC by default; `zitex.sty` falls back to FandolSong from TeX Live). Inkscape is needed only for SVG glyphs or SVG pictures. Emoji pictures need Pillow and a colour emoji font (Noto Color Emoji): `pip install -e ".[pict]"`.

## Quick start

```bash
zitex check -i tests/data/chars.yaml                     # validate
zitex render -i tests/data/chars.yaml -c 森 -s math \
      -x tests/data/lexicon.yaml --collapse -o -      # print one equation
zitex render -i tests/data/chars.yaml -c 森,作 -o figs/   # .tex and .pdf, every style, into figs/
make -C examples/demo                                  # build a small paper
(cd examples/pict && ./build.sh)                       # the picture view: 日 + 月 = 明 and 木 + 木 = 林, with emoji and with oracle bone glyphs
```

From the ZiNets SQLite database instead of a YAML file:

```bash
zitex db-build -i path/to/zi.sqlite3 -o db/zitex.sqlite3  # once: a clean zx_ copy, the original untouched
zitex render -i db/zitex.sqlite3 -c 器,藻 -o figs/       # the same render command
```

Or a self-contained folder, with everything `xelatex` needs (including `zitex.sty`):

```bash
zitex setup -o work/                                   # fonts.yaml for this computer, zitex.sty, samples
zitex extract -c 器,藻,佛 -o work/                     # chars.yaml, lexicon.yaml, main.tex and its snippets (db/zitex.sqlite3 by default; -i PATH for another)
cd work && xelatex main.tex
```

In a document:

```latex
\usepackage{zitex}
...
\zimath{時}   \zimatrix{國}   \zitree{藻}   \ziformula{氢}   \zimath[lang=fr]{森}
\zimath[pict]{明}   \zimath[pict=obs,lang=zh]{林}     % the picture view; pict=obs is a named set of pictures
```

```bash
zitex install-sty                                      # once: lets plain xelatex find zitex.sty
zitex render -i chars.yaml --scan main.tex -x lexicon.yaml
xelatex main.tex
```

A browser app does the same, and lets you review and correct decompositions: `pip install -e ".[ui]"`, then `streamlit run src/ui/streamlit/app.py` (see [`src/ui/streamlit/README.md`](https://github.com/digital-duck/zinets-latex/blob/main/src/ui/streamlit/README.md)).

The step-by-step guide is in [`docs/GUIDE/TUTORIAL.md`](https://github.com/digital-duck/zinets-latex/blob/main/docs/GUIDE/TUTORIAL.md).

## From Python

```python
from zitex import load_yaml, load_lexicon, render_snippet

entries = load_yaml("chars.yaml")
lex = load_lexicon(entries, "lexicon.yaml")
print(render_snippet(entries[0], "math", lex=lex, lang="fr"))
```

## Status

A working prototype. Parsing, validation, the renderers (the four styles and the picture view), the LaTeX package, the build command, the language and font handling, the two data adapters (YAML and the read-only SQLite bridge), `setup` and `extract`, hand revisions, the review app, and the picture sets are done and tested (`pytest -q`). A few tests in `test_pipeline.py` and `test_ui.py` fail on the author's machine and are not related to the picture view.

Not done yet: the hook into the ZiNets app. The decomposition data in the database is still under review (some rows cannot be converted and are listed in `db/`). The data in `tests/data/` is a 29-character sample, partly reviewed, and its glosses and pinyin are drafts. Only a few dozen oracle bone glyphs have been chosen so far (`data/ele_chars/`, exported from Orascope with `scripts/export_picts.py` in that repository), and a calligraphy set is an idea, not built.

The API will change a little as [conceptbook-app](https://github.com/digital-duck/conceptbook-app) starts to use it as a dependency.

## Documentation

- [`docs/GUIDE/TUTORIAL.md`](https://github.com/digital-duck/zinets-latex/blob/main/docs/GUIDE/TUTORIAL.md): tutorial
- [`docs/GUIDE/HOW-IT-WORKS.md`](https://github.com/digital-duck/zinets-latex/blob/main/docs/GUIDE/HOW-IT-WORKS.md): how LaTeX is extended to make zitex work
- [`docs/DEV/claude/readme-zimath.md`](https://github.com/digital-duck/zinets-latex/blob/main/docs/DEV/claude/readme-zimath.md): design and usage of the picture view (`\zimath[pict]`)
- [`examples/pict/`](https://github.com/digital-duck/zinets-latex/blob/main/examples/pict/): the picture view with emoji and oracle bone glyphs; `./build.sh` makes `main.pdf`
- [`docs/paper/arxiv/`](https://github.com/digital-duck/zinets-latex/blob/main/docs/paper/arxiv/): the paper that describes zitex
- [`docs/DEV/claude/spec.md`](https://github.com/digital-duck/zinets-latex/blob/main/docs/DEV/claude/spec.md): grammar, operators and position rules
- [`docs/DEV/claude/readme.md`](https://github.com/digital-duck/zinets-latex/blob/main/docs/DEV/claude/readme.md): development plan and milestones
- [`CLAUDE.md`](CLAUDE.md): architecture notes for working on the code

## Citing

If you use zitex in your work, please cite the paper above (the model). A paper that describes zitex itself is in [`docs/paper/arxiv/`](https://github.com/digital-duck/zinets-latex/blob/main/docs/paper/arxiv/).

```bibtex
@misc{gong2025chinese,
  title         = {A New Exploration into Chinese Characters: from Simplification to Deeper Understanding},
  author        = {Gong, Wen G.},
  year          = {2025},
  eprint        = {2502.19428},
  archivePrefix = {arXiv},
  url           = {https://arxiv.org/abs/2502.19428}
}
```

## License and data attribution

The code is MIT. See [`LICENSE`](LICENSE). The images, data and fonts that come with the repository have their own licences, listed in [`NOTICE`](NOTICE): the oracle bone glyphs are from HUST-OBC and are **CC BY-NC 4.0** (non-commercial use only).

The data in [`db/`](https://github.com/digital-duck/zinets-latex/blob/main/db/) is derived from the ZiNets database and uses definitions from **[CC-CEDICT](https://cc-cedict.org)**, which is licensed **CC BY-SA 4.0**. That data is shared under the same licence, with the changes described in [`db/NOTICE.md`](https://github.com/digital-duck/zinets-latex/blob/main/db/NOTICE.md). The attribution is also stored inside the database file and written at the top of every YAML file that `zitex extract` produces.
