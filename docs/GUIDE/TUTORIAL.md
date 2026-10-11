# zitex Tutorial

This tutorial takes you from one hand-written character to a typeset paper page. About 20 minutes. The commands in sections 2 to 5 and 7 were run as written from an empty folder, section 8 was run against the derived database in `db/`, and the pict example in section 4 (`日 + 月 = 明`) was built and compiled as written (its folder is `examples/pict/`). The fallback example in section 6 uses a placeholder name (`qi-top`) and was not run.

Every command that reads data takes it with **`-i` / `--input`** (there are no positional file arguments). Without `-i`, the commands read `./chars.yaml`.

You need Python 3.10+, XeLaTeX with the `tikz`, `xeCJK`, `fontspec` and `amsmath` packages, and a CJK font. The examples use Noto Serif CJK SC.

## 1. Install

```bash
conda activate zinets2          # or any env with Python 3.10+
cd zinets-latex
pip install -e .                # installs the `zitex` command
zitex --version
```

## 2. Describe a character

A decomposition lives in a YAML file. Create `chars.yaml`:

```yaml
- char: 好
  pinyin: hǎo
  meaning: good
  shape: "⿰女子"

- char: 林
  pinyin: lín
  meaning: woods
  shape: "⿰木木"

- char: 森
  pinyin: sēn
  meaning: forest
  shape: "∴木木木"
```

A character has three dimensions, and each has its own field: **shape** (形, how it is built from strokes and components), **sound** (音, `pinyin`) and **meaning** (義, `meaning`). The `shape` field holds the decomposition as a compact prefix expression, written in Unicode's *Ideographic Description Sequence* (IDS) notation, plus some ZiNets operators for flat patterns. `⿰` puts two parts left and right, so `⿰女子` is 女 on the left of 子. Each operator takes a fixed number of arguments, so no brackets are needed.

| Operator | Layout | Example |
|---|---|---|
| ⿰ ⿲ | left to right (2 or 3 parts) | 好 = `⿰女子` |
| ⿱ ⿳ | top to bottom (2 or 3 parts) | 寺 = `⿱土寸` |
| ⿴ ⿵ ⿶ ⿷ | enclosed (all sides, from above, from below, from the left) | 國 = `⿴囗或` |
| ⿸ ⿹ ⿺ | enclosed from a corner | 病 = `⿸疒丙` |
| ⿻ | overlaid | |
| **∴** | one on top, two below (ZiNets) | 品 = `∴口口口` |
| **∵** | two on top, one below (ZiNets) | 哭 = `∵口口犬` |
| **∷** | a 2×2 grid (ZiNets) | 叕 = `∷又又又又` |
| **⁙** | four corners and a center (ZiNets) | 器 = `⁙口口犬口口` |
| **<pattern>** | any other flat pattern (ZiNets) | `<L-RU-RD>又又又` |

The ZiNets operators are not Unicode IDS. They keep a level with three or more parts as one level, where plain IDS has to nest (`⿱口⿰口口`) and invents intermediate parts that have no meaning. For 器, four 口 around 犬, that matters: it is one level with five parts.

Check the file:

```bash
zitex check -i ./tests/data/chars.yaml
# chars.yaml: 3 entries, 0 warnings
zitex shape -i ./tests/data/chars.yaml
# 好	⿰女子

```

`check` also takes several files, separated by commas, as `-c` does: `zitex check -i chars.yaml,another.yaml`.

## 3. Positions

Every component sits at one of eleven positions, written with short codes:

| Code | Meaning | Code | Meaning |
|---|---|---|---|
| L | left (左) | LU | left-up (左上) |
| R | right (右) | LD | left-down (左下) |
| U | up (上) | RU | right-up (右上) |
| D | down (下) | RD | right-down (右下) |
| M | mid, the center of gravity (中) | Mo | the frame of an enclosure (中外) |

The Chinese names are accepted too, and converted when the file is loaded. The positions of one level, joined by hyphens, form its **pattern**: `L-M`, `U-LD-RD`.

`M` is not only the geometric middle. It is the part that holds the character's center of gravity, which in a two-part character is usually the non-radical part. **A Kangxi radical is peripheral.** So 佛 is 亻 (`L`) + 弗 (`M`), not 亻 (L) + 弗 (R), and 時 is 日 (`L`) + 寺 (`M`). Two radicals, or none, are peers: 双 is 又 (`L`) + 又 (`R`).

When you write `shape`, zitex fills in the positions for you: from the radical rule for `⿰` and `⿱`, and from the operator's fixed pattern for the rest (`⿴` is `Mo-M`, `⿵` is `Mo-D`, `⿸` is `LU-M`). If you want to set them yourself, which is how the SQLite database stores them, write the tree out:

```yaml
- char: 佛
  tree:
    op: ⿰
    parts: [{c: 亻, pos: L}, {c: 弗, pos: M}]
```

`zitex check` warns when a pattern is not allowed for its operator (`W2`), when position regions overlap (`W7`, for example `U-L-R`, which should be `U-LD-RD`), or when a radical is labelled `M` (`W8`). Warnings never stop a build. The full rules are in `docs/DEV/claude/zi-matrix.md`. Deeper nesting and named composites (a part with its own name, like 喿 inside 藻) are in `tests/data/chars.yaml`.

## 4. See the result

Add pinyin and glosses in a lexicon file, `lexicon.yaml`:

```yaml
女: {pinyin: nǚ, gloss: {en: woman, fr: femme}}
子: {pinyin: zǐ, gloss: {en: child, fr: enfant}}
木: {pinyin: mù, gloss: {en: tree, fr: arbre}}
```

Characters in `chars.yaml` already carry their own pinyin and English meaning, so the lexicon only needs the components, and any other languages.

`render` reads `lexicon.yaml` from the current folder when you do not pass `-x`, so with that file name you can leave `-x` out. Passing `-x` uses only the files you name, and ignores the default.

Print one equation (`-o -` means stdout):

```bash
zitex render -i chars.yaml -c 好 -s math -x lexicon.yaml -o -
```

```latex
\[ \underbrace{\overset{\text{nǚ}}{\text{女}}}_{\text{woman}} + \underbrace{\overset{\text{zǐ}}{\text{子}}}_{\text{child}} = \underbrace{\overset{\text{hǎo}}{\text{好}}}_{\text{good}} \]
```

That is plain LaTeX math. In a document it shows pinyin above each piece, its gloss below, and the result as an equation, like a chemical reaction. The same string works in MathJax or KaTeX on a web page.

`render` reads the file you name with `-i` (`--input`), or `./chars.yaml` when you leave `-i` out. By default it renders **every character** in the file, in every style, as `u<hex>-<style>.tex` and `.pdf` (`<hex>` is the character's code point, so 藻 is `u85fb-tree.tex`; `build_manifest.json` in the same folder maps names back to characters), into a `zitex-out/` folder (the folder `zitex.sty` reads). Choose characters with `--char` (`-c`) and say where the output goes with `-o`:

| Command | Result |
|---|---|
| `zitex render -i my.yaml -x lex.yaml` | everything, into `zitex-out/` |
| `zitex render -i my.yaml -c 好,森 -x lex.yaml -o figs/` | every style for 好 and 森, into `figs/` |
| `zitex render -i my.yaml -c 好 -s math -x lex.yaml -o hao` | `hao.tex` and `hao.pdf` (one character, one style: a file stem) |
| `... -o hao.tex` | `hao.tex` only (the suffix picks the format) |
| `... -o hao.pdf` | `hao.pdf` only |
| `... -o -` | print the snippet to stdout |

- Name several characters with commas or spaces: `-c 好,森`, `-c "好 森"`, or `-c 好 -c 森`. A character that is not in the data is named on stderr and skipped.
- One file name cannot hold several outputs. A name without a suffix is a file stem only when you name one character and one style; otherwise it is a directory (created if needed). A `.tex` or `.pdf` suffix with several outputs is an error.
- `--emit tex|pdf|both` overrides the format. If `xelatex` is missing, you get an error after the `.tex` is written.
- `-s` takes one style or a comma list. `-l` can be repeated to render several languages.

There are four styles (`-s`) that `render` builds by default, and a fifth, `pictmath`, that you ask for (see *Add shape* below):

| Style | What it draws |
|---|---|
| `math` | the equation above (default for prose) |
| `formula` | one line: `女 + 子 → 好 (hǎo, good)` |
| `tree` | a tree growing to the right, position on each edge |
| `matrix` | nested boxes laid out by operator (the Zi-Matrix) |
| `pictmath` | the equation as a grid with a picture row: pinyin, character, meaning, picture (opt-in) |

Options for `math`:

```bash
zitex render -i chars.yaml -c 森 -s math -x lexicon.yaml -o - --collapse # 3 × 木 = 森
zitex render -i chars.yaml -c 森 -s math -x lexicon.yaml -o - -l fr # glosses in French
zitex render -i chars.yaml -c 好 -s math -x lexicon.yaml -o - --arrow reaction # use an arrow
zitex render -i chars.yaml -c 好 -s math -x lexicon.yaml -o - --result paren # 好 (good) instead of gloss below
zitex render -i chars.yaml -c 好 -s math -x lexicon.yaml -o - --show-pos # subscript each piece with its position
```

`--arrow role` labels the arrow with the phonetic component when the entry has a `role:` mapping (for example `忄 + 每 —(sound: měi)→ 悔`). If a language has no gloss for a character, zitex falls back to English.

### Several readings of one character

Which part of a character carries the meaning and which the sound is an interpretation, and interpretations differ. An entry can keep several, and you choose one when you render. Add this entry to your `chars.yaml`, and these two lines to `lexicon.yaml`:

```yaml
# chars.yaml
- char: 虹
  pinyin: hóng
  meaning: rainbow
  shape: "⿰虫工"
  readings:
    - name: author
      role: {虫: semantic, 工: semantic}
    - name: dictionary
      role: {虫: semantic, 工: phonetic}
```

```yaml
# lexicon.yaml
虫: {pinyin: chóng, gloss: {en: insect}}
工: {pinyin: gōng, gloss: {en: work}}
```

```bash
zitex render -i chars.yaml -c 虹 -s math -x lexicon.yaml -o - --arrow role # the first reading: 虫 + 工 = 虹
zitex render -i chars.yaml -c 虹 -s math -x lexicon.yaml -o - --arrow role --reading dictionary # 虫 + 工 —(sound: gōng)→ 虹
```

The first reading is the default. A reading changes the colours of the pieces and the label on the arrow, and nothing else. In a paper, write `\zimath[reading=dictionary]{虹}`, or `\zitexsetreading{dictionary}` to change the default for the rest of the document.

### Add shape: the picture row (`pict`)

A character has three dimensions: sound, meaning and shape. `math` shows the first two. The `pictmath` style adds the third, as a row of small pictures under the meanings, so that `日 + 月 = 明` carries pinyin, character, meaning and picture for every piece. Add a `pict` to each lexicon entry: a picture file, or an emoji. Chinese is just another language here: give each gloss in as many languages as you like.

```yaml
# lexicon.yaml
日: {pinyin: rì,   gloss: {en: sun,    zh: 太阳}, pict: "☀️"}
月: {pinyin: yuè,  gloss: {en: moon,   zh: 月亮}, pict: "🌙"}
明: {pinyin: míng, gloss: {en: bright, zh: 明亮}, pict: "✨"}
```

```yaml
# chars.yaml
- char: 明
  pinyin: míng
  meaning: bright
  shape: "⿰日月"
```

```latex
% main.tex
\documentclass{article}
\usepackage{zitex}
\begin{document}
\zimath[pict]{明}
\zimath[pict,lang=zh]{明}
\end{document}
```

```bash
zitex render -i chars.yaml --scan main.tex -x lexicon.yaml -l en -l zh
xelatex main.tex
```

The result, once per language:

```
   rì          yuè          míng            rì          yuè          míng
   日     +     月     =     明             日     +     月     =     明
   sun         moon         bright          太阳        月亮         明亮
   ☀️          🌙           ✨              ☀️          🌙           ✨
```

(In the PDF the bottom row is real pictures.) What to know:

- **It is a grid.** Each row lines up across all the pieces, so the pictures sit on one line and the meanings on another. A row that nothing fills is left out, and a piece with no picture has an empty cell. Pieces inside brackets (木 + 目 inside 想) each keep their own column.
- **`pict` is optional, and has an order of preference:** a picture file, else an emoji, else nothing. A picture file is the `pict:` value (relative to the lexicon file), or a file named `u<hex>.png` (日 is `u65e5.png`; `.jpg`, `.pdf` and `.svg` work too) in the folder named by `ZITEX_PICT_DIR`. A lexicon entry that is not an image file is taken as an emoji. XeLaTeX cannot print colour emoji, so zitex draws it into a PNG first (it needs Pillow and an emoji font, Noto Color Emoji by default). The files go next to the snippets, in `zitex-out/picts/`.
- **The meaning has an order too:** the gloss (a concrete phrase), else the entry's `concept` (written in ALL CAPS, such as `HAND`), else its `category` (`HUMAN-BODY`), else nothing. Give an entry `concept:` and `category:` in the lexicon the same way as `gloss:`.
- **The size is fixed**, so the picture row is regular. Set it in a `.env` file in the folder where you run `zitex` (or in the environment). `.env.example` lists every setting:

  ```
  ZITEX_PICT_HEIGHT=1.8em
  ZITEX_PICT_WIDTH=1.8em
  ZITEX_MEANING_WIDTH=6em      # meanings wrap here
  ZITEX_MEANING_SENSES=3       # show at most 3 '/'-separated senses
  ```

- **Oracle bone glyphs.** The pictures can be oracle bone glyphs. Orascope's `scripts/export_picts.py` exports one starred glyph per elemental character, named `u<hex>.png`, with a matching `lexicon.yaml`, into `data/ele_chars/`. Then run `ZITEX_PICT_DIR=data/ele_chars zitex render -i chars.yaml --scan main.tex -x data/ele_chars/lexicon.yaml`. The glyphs come from HUST-OBC (CC BY-NC 4.0): keep the attribution.
- **Several sets of pictures.** A pict comes from the lexicon key `pict`, which is the default set. A second set has its own key, `pict_obs: u65e5.png`, and you pick it with `\zimath[pict=obs]{明}`. So one document can show emoji in one equation and oracle bone glyphs in the next (`examples/pict/main.tex` does exactly that, for 明 and for 虫 + 工 = 虹). A set does not fall back to the default: a character with no picture in the set has an empty cell. A set can also be a folder, `<ZITEX_PICT_DIR>/obs/u<hex>.png`. Orascope's `export_picts.py --chars 日月明 --set obs` writes such a set.
- **It needs XeLaTeX.** A snippet with pictures is not for MathJax; plain `\zimath` still is.
- **It is opt-in.** `\zimath{明}` is unchanged. `zitex render` without `-s` does not build `pictmath`: either write `\zimath[pict]` and use `--scan`, or name the style, as in `zitex render -i chars.yaml -c 明 -s pictmath -x lexicon.yaml -l zh` (`-s pictmath-obs` for the set `obs`).

The design and the reasons are in `docs/DEV/claude/readme-zimath.md`.

## 5. Use it in a paper

zitex does the work in Python and leaves LaTeX only the last step. The flow is: write `\zi` commands, run `zitex render --scan` to make the snippets, then run XeLaTeX.

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

Commands: `\zi[style=…,lang=…]{字}`, and the shorthands `\zitree`, `\zimatrix`, `\ziformula` and `\zimath`. The argument is one character. `\zimath[pict]{字}` is the equation with a picture row (see section 4).

Render only what the document uses, then typeset:

```bash
zitex render -i chars.yaml --scan main.tex -x lexicon.yaml -l en -l fr --collapse
xelatex main.tex
```

`--scan` reads `main.tex` and writes just those snippets (`.tex` only, since LaTeX typesets them) into `zitex-out/` (here `u597d-math-en.tex`, `u68ee-math-fr.tex` and `u68ee-matrix.tex`). XeLaTeX must be able to find `zitex.sty`. There are three ways, and the first is the simplest:

- **Put it next to your document.** `zitex setup -o .` copies `zitex.sty` into the folder (and writes a `fonts.yaml` for your computer, see section 8). The folder is then self-contained, and you can zip it or upload it to Overleaf.
- **Install it once for every document.** `zitex install-sty` copies it into your personal TeX folder (`TEXMFHOME`, usually `~/texmf`), and plain `xelatex main.tex` works from then on. Run it again after upgrading zitex. `zitex install-sty --dir DIR` installs into another TeX tree.
- **Point XeLaTeX at it for one run:** `TEXINPUTS=<folder of zitex.sty>: xelatex main.tex`. The folder is the `zitex` package folder (`python -c "import zitex, pathlib; print(pathlib.Path(zitex.__file__).parent)"`).

Options such as `--collapse` apply to every `math` snippet. In the document, `\zitexsetlang{fr}` changes the default language and `\zitexsetpath{dir}` changes where snippets are read from.

If a snippet is missing, LaTeX prints a warning (`Missing zitex-out/…; run zitex render`) and shows a red `[字?]` in the page, so the build does not break.

To get stand-alone figures instead, leave out `--scan`:

```bash
zitex render -i chars.yaml -c 好,森 -s math,matrix -x lexicon.yaml -o figs/
```

`--emit` is `both` by default (snippets and compiled PDFs); `tex` or `pdf` writes just one. PDFs use Noto Serif CJK SC unless you pass `--font`.

A complete example is in `examples/demo/`; run `make -C examples/demo`.

## 6. Characters your font cannot draw

Some of the paper's 422 elemental characters have no Unicode code point, and some rare ones are missing from common fonts. Check what you have:

```bash
zitex fonts -i chars.yaml
# primary: Noto Serif CJK SC   fallbacks: -
# 6 components: 6 in the primary font, 0 via fallback, 0 missing
```

`zitex setup -o .` writes a `fonts.yaml` made for the fonts on your computer (section 8). To write one by hand, describe the fallbacks in `fonts.yaml`:

```yaml
primary: Noto Serif CJK SC
fallbacks: [AR PL UMing CN]          # tried in order
components:
  "{qi-top}": {svg: glyphs/qi-top.svg}   # a component with no code point, drawn from an image
  甲: {alias: 日}                          # draw a different character instead
```

Write such a component by name in `shape`: `⿰日{qi-top}`. Then pass `--fonts fonts.yaml` to `render` (and to `fonts`: `zitex fonts -i chars.yaml --fonts fonts.yaml`). A glyph that nothing can draw is shown as a boxed `U+20009` (or the name) and listed in the build output. `zitex fonts --strict` exits with status 1 if any component is missing. SVG glyphs are converted with Inkscape into `zitex-out/glyphs/`.

## 7. From Python

```python
from zitex import load_yaml, load_lexicon, render_snippet

entries = load_yaml("chars.yaml")
lex = load_lexicon(entries, "lexicon.yaml")
hao = entries[0]

print(render_snippet(hao, "math", lex=lex, lang="fr"))
print(render_snippet(hao, "formula", lex=lex))
```

`render_snippet(entry, style, fonts=None, **options)` returns a LaTeX string. Use `zitex.render_with` if you also want the list of missing glyphs. `zitex.build.build(...)` writes files, as the command does.

## 8. Using the SQLite database

Everything above reads a `chars.yaml`. The same commands also read the ZiNets SQLite database, through a second data adapter, so you can render the thousands of characters in it without writing YAML by hand.

```bash
zitex db-build -i path/to/zi.sqlite3 -o db/zitex.sqlite3 --report db/zitex-quarantine.csv   # once, and again after the database changes
zitex patterns -i db/zitex.sqlite3                                  # how often each pattern occurs
zitex render -i db/zitex.sqlite3 -c 器,藻 -o figs/                  # render straight from the database
zitex extract -c 器,藻 -o work/                                  # or extract them into a folder, to read and typeset
```

- **Your database is never changed.** `db-build` opens it read only, and writes a small separate file, `zitex.sqlite3`, next to it (four tables, all starting with `zx_`). It checks at the end that your file is byte for byte what it was. You can delete the new file and rebuild it any time.
- **Rows that cannot be converted safely are not guessed at.** They are left out, and listed with the reason in the report: for example a position cell that holds two parts, or a part that is `?`. Characters whose parts have no decomposition of their own stay as leaves.
- **Every command accepts the database in place of the YAML:** `check`, `shape`, `patterns`, `fonts`, `render` and `extract`. You can also point them at the raw working database (`zi.sqlite3`): it is converted in memory and nothing is written.
- **Pinyin and glosses** come from the database too (tone numbers are converted to tone marks), so equations have labels without a lexicon file. A `lexicon.yaml` in the current folder, or `-x`, replaces what the database says for the characters it names.
- **`--depth N`** limits how many levels a tree is expanded (default: all, so 藻 goes down to 口 and 木).

### A self-contained working folder: setup, extract, xelatex

Three commands take you from the database to a PDF, in one folder that has everything it needs:

```bash
zitex setup -o work/                                       # once per folder
zitex extract -c 器,藻,佛 -o work/                          # as often as you like
cd work && xelatex main.tex
```

- **`zitex setup -o work/`** writes `zitex.sty`, `fonts.yaml`, `fallback.yaml` and `glyphs/demo.svg`.
  - `zitex.sty` is copied **into the folder**, so `xelatex` finds it next to `main.tex`. Nothing is installed in your home folder, and you can zip the folder and send it, or upload it to Overleaf. (`zitex install-sty` still installs it globally, if you prefer.) It is brought up to date whenever it differs from your version of zitex, because it has to match the file names zitex writes.
  - `fonts.yaml` is made for **this computer**. The primary font is the first of the usual CJK fonts found (Noto Serif CJK SC first). Each fallback is chosen because it adds characters the others lack, and a font that adds none is left out. The primary font and the `\setCJKmainfont` line of `main.tex` name the same font, so the two cannot drift apart.
  - `fallback.yaml` and `glyphs/` are samples for trying the fallback (see section 6). Files you may have edited are kept unless you pass `--force`.
- **`zitex extract -c ... -o work/`** writes `chars.yaml` and `lexicon.yaml` for the characters you name with `-c` (in that order, and with no `db-` prefix), then `main.tex`, a document with every style for every character, like `examples/demo/main.tex`. It also renders the snippets `main.tex` uses into `work/zitex-out/`, using the folder's `fonts.yaml`, so the next command needs nothing else.
  - **The database** is `-i PATH` (`--input`). Without it, `extract` uses `db/zitex.sqlite3`, looked for in this folder and then in each parent folder (like git finds its repository, so it works from `work/` too), then in the zitex checkout, and `$ZITEX_DB` is tried first. It says which file it used. If it finds none, it says where it looked.
  - **At most 60 characters** are extracted, because that is as much as `main.tex` should hold. With more (for instance no `-c` at all, which means "all of them"), the first 60 are kept and a warning says so. Name the ones you want with `-c`.
  - Running it again on the same folder **overwrites** `chars.yaml`, `lexicon.yaml`, `main.tex` and the snippets. Keep a `main.tex` you wrote yourself in another folder (or copy it back after extracting).
  - `-c` takes a phrase as well as a list: `-c 守株待兔` is the same as `-c 守,株,待,兔`. Repeats are dropped and punctuation is skipped.
  - `-o` defaults to the current folder.
  - `--annotation minimal|demo` picks the `main.tex`. `minimal` (the default) lists every style for every character. `demo` writes an annotated paper for your characters: abstract, figures, a table, a **Syntax** note after each block of markup, and a summary of the commands. Use it as a starting point for a real paper (copy it before you edit, because `extract` writes it again each time). `zitex render --scan` ignores `%` comments and verbatim listings, so a listing can show `\zitexsetlang{fr}` without changing the output.
- **Afterwards** the YAML files are ordinary input: `zitex render --fonts fonts.yaml -o figs/` works in that folder (`chars.yaml` and `lexicon.yaml` are picked up by default), and you can edit `main.tex` and run `zitex render --scan main.tex` again.

How the adapters work, what was found in the database, and what is still open is in `docs/DEV/claude/db-integration.md`.

## 9. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Missing character: There is no ∴` | the ZiNets operators must be declared CJK: `\xeCJKDeclareCharClass{CJK}{"2234,"2235,"2237}`. `zitex.sty` and `--emit pdf` do this for you |
| `Got unexpected extra argument (chars.yaml)` | files are given with `-i`, not as an argument: `zitex render -i chars.yaml` |
| `no input: there is no chars.yaml in this folder` | pass `-i PATH`, or run the command in the folder that holds `chars.yaml` |
| `Invalid value for '-i' / '--input': File … does not exist` | wrong path. For `check -i a.yaml,b.yaml` the message is `input '…' is not a file` |
| `not in chars.yaml: 虹` | the character has no entry in the file. Add it (section 4 shows one), or check the spelling |
| `mapping values are not allowed here` (YAML) | a value containing `: ` must be in quotes |
| `W2` warnings | the positions of a level make a pattern the operator does not allow (see section 3). Fix the data, or ignore if it is intended |
| a red `[字?]` in the page | the snippet was not built. Run `zitex render -i chars.yaml --scan main.tex` in the folder that holds `main.tex` |
| `File 'zitex.sty' not found` | see section 5: `zitex setup -o .`, or `zitex install-sty` |
| a picture row is empty, or a pict is missing | the picture was not found: put `u<hex>.png` in `ZITEX_PICT_DIR` or name the file in the lexicon. An emoji needs Pillow and a colour emoji font (`ZITEX_EMOJI_FONT`) |
| `\zimath[pict]` shows a red `[字?]` | the `pictmath` snippet was not built. It is not in the default styles: use `--scan`, or `-s pictmath` |
| the grid is wider than the page | lower `ZITEX_MEANING_WIDTH` or `ZITEX_MEANING_SENSES` in `.env` |
| a box labelled `U+XXXXX` | no font draws that code point. Add a fallback font or an SVG in `fonts.yaml` |

## Where next

- `docs/DEV/claude/spec.md`: the exact grammar, operator table and position rules
- `tests/data/chars.yaml`: 29 sample characters, including deep nesting and named composites
- the paper that defines the 422 elemental characters and the eleven positions: see the README
