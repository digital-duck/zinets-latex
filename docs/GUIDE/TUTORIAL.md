# zitex Tutorial

This tutorial takes you from one hand-written character to a typeset paper page. About 20 minutes. The commands in sections 1 to 5 were run as written; the fallback example in section 6 uses placeholder names (`qi-top`) and was not run.

You need Python 3.10+, XeLaTeX with the `tikz`, `xeCJK`, `fontspec` and `amsmath` packages, and a CJK font. The examples use Noto Serif CJK SC.

## 1. Install

```bash
conda activate zinets2          # or any env with Python 3.10+
cd zinets-latex
pip install -e .                # installs the `zitex` command
zitex --version
```

## 2. Describe a character

A decomposition lives in a YAML file. Create `my.yaml`:

```yaml
- char: 好
  pinyin: hǎo
  meaning: good
  ids: "⿰女子"

- char: 林
  pinyin: lín
  meaning: woods
  ids: "⿰木木"

- char: 森
  pinyin: sēn
  meaning: forest
  ids: "∴木木木"
```

`ids` is a compact prefix expression. `⿰` puts two parts left and right, so `⿰女子` is 女 on the left of 子. Each operator takes a fixed number of arguments, so no brackets are needed.

| Operator | Layout | Example |
|---|---|---|
| ⿰ ⿲ | left to right (2 or 3 parts) | 好 = `⿰女子` |
| ⿱ ⿳ | top to bottom (2 or 3 parts) | 寺 = `⿱土寸` |
| ⿴ ⿵ ⿶ ⿷ | enclosed (all sides, top, bottom, left) | 國 = `⿴囗或` |
| ⿸ ⿹ ⿺ | enclosed from a corner | 病 = `⿸疒丙` |
| ⿻ | overlaid | |
| **∴** | one on top, two below (ZiNets) | 品 = `∴口口口` |
| **∵** | two on top, one below (ZiNets) | 哭 = `∵口口犬` |

The last two are not Unicode IDS. They keep a triangular pattern as one unit, where plain IDS would write `⿱口⿰口口` and lose that.

Check the file:

```bash
zitex check my.yaml
# my.yaml: 3 entries, 0 warnings
zitex ids my.yaml
# 好	⿰女子
```

## 3. Positions

Every component has one of the paper's eleven positions: 上 下 左 右 中 左上 右上 左下 右下 中内 中外. When you write `ids`, zitex fills in the default position for each operator (左 and 右 for `⿰`, and so on).

If you want to set positions yourself, which is how the SQLite database stores them, write the tree out:

```yaml
- char: 時
  tree:
    op: ⿰
    parts: [{c: 日, pos: 左}, {c: 寺, pos: 右}]
```

If a position does not fit its operator, `zitex check` prints a warning such as `W2 時: '日' pos '上' differs from ⿰ default '左'`. Warnings never stop a build. Deeper nesting and named composites (a part with its own name, like 喿 inside 藻) are in `tests/data/chars.yaml`.

## 4. See the result

Add pinyin and glosses in a lexicon file, `lex.yaml`:

```yaml
女: {pinyin: nǚ, gloss: {en: woman, fr: femme}}
子: {pinyin: zǐ, gloss: {en: child, fr: enfant}}
木: {pinyin: mù, gloss: {en: tree, fr: arbre}}
```

Characters in `my.yaml` already carry their own pinyin and English meaning, so the lexicon only needs the components, and any other languages.

Print one equation:

```bash
zitex render 好 -f my.yaml -s math -x lex.yaml
```

```latex
\[ \underbrace{\overset{\text{nǚ}}{\text{女}}}_{\text{woman}} + \underbrace{\overset{\text{zǐ}}{\text{子}}}_{\text{child}} = \underbrace{\overset{\text{hǎo}}{\text{好}}}_{\text{good}} \]
```

That is plain LaTeX math. In a document it shows pinyin above each piece, its gloss below, and the result as an equation, like a chemical reaction. The same string works in MathJax or KaTeX on a web page.

There are four styles (`-s`):

| Style | What it draws |
|---|---|
| `math` | the equation above (default for prose) |
| `formula` | one line: `女 + 子 → 好 (hǎo, good)` |
| `tree` | a tree growing to the right, position on each edge |
| `matrix` | nested boxes laid out by operator (the Zi-Matrix) |

Options for `math`:

```bash
zitex render 森 -f my.yaml -s math -x lex.yaml --collapse            # 3 × 木 = 森
zitex render 森 -f my.yaml -s math -x lex.yaml -l fr                 # glosses in French
zitex render 好 -f my.yaml -s math -x lex.yaml --arrow reaction      # use an arrow
zitex render 好 -f my.yaml -s math -x lex.yaml --result paren        # 好 (good) instead of gloss below
zitex render 好 -f my.yaml -s math -x lex.yaml --show-pos            # subscript each piece with its position
```

`--arrow role` labels the arrow with the phonetic component when the entry has a `role:` mapping (for example `忄 + 每 —(sound: měi)→ 悔`). If a language has no gloss for a character, zitex falls back to English.

## 5. Use it in a paper

zitex does the work in Python and leaves LaTeX only the last step. The flow is: write `\zi` commands, run `zitex build` to make snippets, then run XeLaTeX.

`main.tex`:

```latex
\documentclass{article}
\usepackage{zitex}
\begin{document}
\zimath{好}
\zimath[lang=fr]{森}
\zimatrix{森}
\end{document}
```

Commands: `\zi[style=…,lang=…]{字}`, and the shorthands `\zitree`, `\zimatrix`, `\ziformula` and `\zimath`. The argument is one character.

Build only what the document uses, then typeset:

```bash
zitex build my.yaml --scan main.tex -x lex.yaml -l en -l fr --collapse -o zitex-out
TEXINPUTS=/path/to/zinets-latex/tex: xelatex main.tex
```

`--scan` reads `main.tex` and writes just those snippets into `zitex-out/` (here `好-math-en.tex`, `森-math-fr.tex` and `森-matrix.tex`). `TEXINPUTS` tells XeLaTeX where `zitex.sty` is; skip it if you copied the file next to your document or installed it in your TeX tree. Build options such as `--collapse` apply to every `math` snippet. In the document, `\zitexsetlang{fr}` changes the default language and `\zitexsetpath{dir}` changes where snippets are read from.

If a snippet is missing, LaTeX prints a warning (`Missing zitex-out/…; run zitex build`) and shows `[字]` in the page, so the build does not break.

To get stand-alone figures instead, use `--emit`:

```bash
zitex build my.yaml -c 好,森 -s math,matrix --emit both -x lex.yaml -o figs
```

`tex` writes snippets, `pdf` writes compiled PDFs, and `both` writes both. PDFs use Noto Serif CJK SC unless you pass `--font`.

A complete example is in `examples/demo/`; run `make -C examples/demo`.

## 6. Characters your font cannot draw

Some of the paper's 422 elemental characters have no Unicode code point, and some rare ones are missing from common fonts. Check what you have:

```bash
zitex fonts my.yaml
# primary: Noto Serif CJK SC   fallbacks: -
# 6 components: 6 in the primary font, 0 via fallback, 0 missing
```

Describe fallbacks in `fonts.yaml`:

```yaml
primary: Noto Serif CJK SC
fallbacks: [AR PL UMing CN]          # tried in order
components:
  "{qi-top}": {svg: glyphs/qi-top.svg}   # a component with no code point, drawn from an image
  甲: {alias: 日}                          # draw a different character instead
```

Write such a component by name in `ids`: `⿰日{qi-top}`. Then pass `--fonts fonts.yaml` to `build` or `render`. A glyph that nothing can draw is shown as a boxed `U+20009` (or the name) and listed in the build output. `zitex fonts --strict` exits with status 1 if any component is missing. SVG glyphs are converted with Inkscape into `zitex-out/glyphs/`.

## 7. From Python

```python
from zitex import load_yaml, load_lexicon, render_snippet

entries = load_yaml("my.yaml")
lex = load_lexicon(entries, "lex.yaml")
hao = entries[0]

print(render_snippet(hao, "math", lex=lex, lang="fr"))
print(render_snippet(hao, "formula", lex=lex))
```

`render_snippet(entry, style, fonts=None, **options)` returns a LaTeX string. Use `zitex.render_with` if you also want the list of missing glyphs. `zitex.build.build(...)` writes files, as the command does.

## 8. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Missing character: There is no ∴` | the triangle operators must be declared CJK: `\xeCJKDeclareCharClass{CJK}{"2234,"2235}`. `zitex.sty` and `--emit pdf` do this for you |
| `Invalid value for 'FILES...': File … does not exist` | wrong path to the YAML file |
| `mapping values are not allowed here` (YAML) | a value containing `: ` must be in quotes |
| `W2` warnings | a position that does not match the operator default. Fix the data, or ignore if it is intended |
| `[字]` in the page | the snippet was not built. Run `zitex build … --scan main.tex` |
| a box labelled `U+XXXXX` | no font draws that code point. Add a fallback font or an SVG in `fonts.yaml` |

## Where next

- `docs/DEV/claude/spec.md`: the exact grammar, operator table and position rules
- `tests/data/chars.yaml`: 23 reviewed characters, including deep nesting and named composites
- the paper that defines the 422 elemental characters and the eleven positions: see the README
