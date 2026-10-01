# zitex

Chinese character decompositions as typeset equations, trees and diagrams, through XeLaTeX.

Write what a character is made of, once, in YAML:

```yaml
- char: 時
  pinyin: shí
  meaning: time
  ids: "⿰日寺"
```

and get it back as a reaction-style equation with pinyin above and a gloss below each piece:

```
 rì     sì          shí
 日  +  寺   ──→   時
 sun   temple       time
```

(See `examples/m2/equations.pdf` for the real output, and `examples/demo/` for a complete paper.)

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

- **Compact input.** Unicode IDS strings, such as `⿱艹⿰氵喿(⿱品(∴口口口)木)` for 藻, or explicit YAML trees with a position on every component.
- **Two ZiNets operators.** `∴` (one on top, two below: 品, 森) and `∵` (two on top, one below: 哭) keep triangular patterns as single units, which standard IDS cannot.
- **Chemistry-style extras.** Repeats collapse (`3 × 木 = 森`), and the arrow can carry the reason for the combination (`忄 + 每 —(sound: měi)→ 悔`).
- **Several languages.** Glosses come from a lexicon file and fall back to English.
- **Fonts that fall short.** Fallback fonts, SVG images for components with no code point, and a coverage report.
- **Two outputs.** `.tex` snippets to `\input` into a paper, and compiled PDF figures.
- **Web-ready.** The `math` output uses only commands that MathJax and KaTeX also understand.

## Install

```bash
pip install -e .          # Python 3.10+, installs the `zitex` command
```

You also need XeLaTeX with `tikz`, `xeCJK`, `fontspec` and `amsmath`, and a CJK font (Noto Serif CJK SC by default). Inkscape is needed only for SVG glyphs.

## Quick start

```bash
zitex check tests/data/chars.yaml                     # validate
zitex render 森 -f tests/data/chars.yaml -s math \
      -x tests/data/lexicon.yaml --collapse           # print one equation
make -C examples/demo                                  # build a small paper
```

In a document:

```latex
\usepackage{zitex}
...
\zimath{時}   \zimatrix{國}   \zitree{藻}   \ziformula{氢}   \zimath[lang=fr]{森}
```

```bash
zitex build chars.yaml --scan main.tex -x lexicon.yaml -o zitex-out
xelatex main.tex
```

The step-by-step guide is in [`docs/GUIDE/TUTORIAL.md`](docs/GUIDE/TUTORIAL.md).

## From Python

```python
from zitex import load_yaml, load_lexicon, render_snippet

entries = load_yaml("chars.yaml")
lex = load_lexicon(entries, "lexicon.yaml")
print(render_snippet(entries[0], "math", lex=lex, lang="fr"))
```

## Status

A working prototype. Parsing, validation, all four renderers, the LaTeX package, the build command, the language and font handling are done and tested (`pytest -q`).

Not done yet: the bridge to the ZiNets SQLite database (the decomposition data there is still under review, so for now zitex works from YAML files), and the hook into the ZiNets app. The data in `tests/data/` is a reviewed 23-character sample, and its glosses and pinyin are drafts.

The API will change a little as [conceptbook-app](https://github.com/digital-duck/conceptbook-app) starts to use it as a dependency.

## Documentation

- [`docs/GUIDE/TUTORIAL.md`](docs/GUIDE/TUTORIAL.md): tutorial
- [`docs/DEV/claude/spec.md`](docs/DEV/claude/spec.md): grammar, operators and position rules
- [`docs/DEV/claude/readme.md`](docs/DEV/claude/readme.md): development plan and milestones
- [`CLAUDE.md`](CLAUDE.md): architecture notes for working on the code

## Citing

If you use zitex in your work, please cite the paper above:

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

## License

MIT. See [`LICENSE`](LICENSE).
