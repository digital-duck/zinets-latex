# `\zimath[pict]`: sound, shape and meaning in one equation

Status: prototype, built 2026-10-11, covered by `tests/test_pict.py` (20 tests). The author has not yet validated it.

## 1. The idea

`\zimath` already reads like a chemical reaction: `日 + 月 = 明`, with pinyin above each piece and a gloss below. `\zimath[pict]` adds the third dimension of a character, its **shape**, so that every piece carries all three:

| Dimension | Row | Source |
|---|---|---|
| sound (音) | pinyin, above the character | lexicon `pinyin` |
| the character | the middle row, joined by `+` and `=` | the decomposition tree |
| meaning (義) | a short phrase, in any language | lexicon `gloss`, else `concept`, else `category` |
| shape (形) | a picture: an oracle bone glyph, a small image or an emoji | lexicon `pict`, or `u<hex>.png` in `ZITEX_PICT_DIR` |

The name `pict` (from *pictograph*) was chosen by the author. Chinese characters began as pictographs, and the picture row visualises them again. `shape` was not used because zitex already uses `shape` for the compact decomposition string (`⿰日月`).

```
   rì          yuè          míng
   日     +     月     =     明
   sun         moon         bright
   ☀️          🌙           ✨
```

Every row is optional. A row nobody fills is left out, and a character with no pict has an empty cell.

## 2. Design

### 2.1 A grid, not stacked labels (the layout decision)

The existing `math` style puts pinyin in `\overset{}` and the gloss in `\underbrace{}_{}` around each term. That keeps the equation MathJax-safe, but every term is laid out on its own: a term with a picture is taller than its neighbours, and pictures of different heights do not line up.

`pictmath` instead builds **one `array`**. There is one column per term, with the operators (`+`, `=`, brackets) as columns of their own, and one row per dimension. Each row therefore lines up across all terms: the picts share one line, the meanings another. `array` is supported by MathJax too, but images are not, so a snippet with picts is for XeLaTeX.

The cost is horizontal space: a grid is as wide as its widest cell in every column. That is why meanings wrap (`ZITEX_MEANING_WIDTH`) and are cut to a few senses (`ZITEX_MEANING_SENSES`).

### 2.2 A separate style, opt-in

The grid is the new style `pictmath` (`render.render_pictmath`), registered in `STYLES` but **not** in `DEFAULT_STYLES`. So:

- `\zimath{字}` is unchanged, and so is every existing snippet and test.
- `\zimath[pict]{字}` (or `pict=true`) selects `pictmath`. `pict=false` is the ordinary `math`.
- `zitex render` without `-s` does not build it. Name it with `-s pictmath`, or let `--scan` find `\zimath[pict]` in the document.
- Snippet names follow the existing rule and carry the language: `u660e-pictmath-en.tex`.

Three places have to agree on this, and `CLAUDE.md` already requires it for the other styles:

| Place | What it does |
|---|---|
| `build.snippet_name` / `LANG_STYLES` | `pictmath` is a language-dependent style, so the name ends in `-<lang>` |
| `zitex.sty` | the `pict` key; when the style is `math` it becomes `pictmath`; `\zitex@name` adds the language |
| `build.scan_tex` | `pict` or `pict=true` on `\zimath` turns the style into `pictmath` (`\zitree[pict]` is ignored) |

### 2.3 The meaning rule

`Lexicon.get_meaning(ch, lang)` returns what is printed under a character:

1. the **gloss** in `lang`, else English, else any language (a concrete phrase: *hand*);
2. else the **concept** (ALL CAPS: `HAND`);
3. else the **concept category** (`HUMAN-BODY`);
4. else nothing (a rare character).

The plain `math` style uses the same rule, so a character with only a concept now shows it instead of an empty label. Nothing changes for characters that already have a gloss.

Concept and category come from Orascope, which keeps `concept` (ALL CAPS, `|`-separated) in `obc_chars` and `concept_category` in `obc_ele_chars`. The ALL-CAPS convention keeps a concept visibly different from a word meaning.

### 2.4 The pict rule

`Lexicon.get_pict(ch)` returns the first that exists:

1. an **image**: the lexicon entry's `pict:` file (relative to the lexicon file, then to `ZITEX_PICT_DIR`), or else `u<hex>.png` / `.jpg` / `.jpeg` / `.pdf` / `.svg` in `ZITEX_PICT_DIR`;
2. an **emoji**: a `pict:` value that is not an image file;
3. nothing.

Two properties matter for the code:

- **Emoji become pictures.** XeLaTeX cannot print colour emoji fonts, so an emoji is drawn to a trimmed PNG with Pillow and Noto Color Emoji (`lexicon.emoji_to_png`). An emoji only counts as available when Pillow and an emoji font are found, so the renderer never promises a picture it cannot make.
- **Naming is pure, writing is separate.** `pict_name(ch)` returns the file name inside `<out>/picts/` (`u65e5.png`) without touching the disk, so rendering stays a pure function of the data. `stage_picts(chars, outdir)` then copies or draws the files. `build()` calls it and records the names in `build_manifest.json` (`"picts": [...]`). The single-file path of `zitex render` and the preview in the app call it too. If a picture already lives in `<out>/picts`, it is not copied onto itself.

SVG picts go through the existing `fonts.svg_to_pdf` and so need Inkscape.

### 2.5 Fixed size, from `.env`

Every pict is set in a box of the same size, so the picture row is regular whatever the images are: `\makebox[\zipictwidth]{\includegraphics[height=\zipictheight,width=\zipictwidth,keepaspectratio]{…}}`. A picture is scaled to fit and keeps its shape. The sizes are TeX lengths in `\zipictheight`, `\zipictwidth` and `\zimeaningwidth`, defined with `\providecommand` at the top of each snippet. The values come from the environment or a `.env` file in the current folder (`zitex.config`, template in `.env.example`); a value that is not a plain length falls back to the default. Because they are `\providecommand`, a document can still override them: define the macro before the first `\zimath[pict]`.

### 2.6 Nested composites

A part with no name of its own (an anonymous composite, like 木 + 目 inside 想) stays in brackets, as in `math`, but each of its parts still gets its own column, between `\Bigl(` and `\Bigr)`. So the picture and meaning rows keep working inside brackets. `--collapse` (`3 × 木`) is honoured: the multiplier sits in the character row.

### 2.7 Named sets of pictures

A document can use several sets of pictures. `\zimath[pict]` uses the default set (the lexicon's `pict`, and `u<hex>.png` in `ZITEX_PICT_DIR`). `\zimath[pict=obs]` uses the set named `obs`:

- the lexicon key is `pict_obs` (any `pict_<name>` key defines the set `<name>`); a relative file is read relative to that lexicon file;
- or the folder `<ZITEX_PICT_DIR>/obs/u<hex>.png`;
- the same preference applies inside the set: image, else emoji, else nothing. A character with no entry in the set gets an empty cell. The set does not fall back to the default set, so a missing glyph is visible and not silently replaced by an emoji.

The set is part of the style name, `pictmath-obs`, so the snippet is `u660e-pictmath-obs-zh.tex` and its pictures are `picts/u65e5-obs.png` (the set name is in the file name, so two sets never overwrite each other). In `zitex.sty` the `pict` key keeps its value: `true` gives `pictmath`, any other value `pictmath-<value>`, `false` leaves `math`; a `\newif\ifzitex@haslang` flag says whether the name carries the language. `scan_tex`, `snippet_name` and `render.split_style` do the same on the Python side, and the CLI accepts `-s pictmath-obs`.

## 3. Usage

### 3.1 In a document

```latex
\usepackage{zitex}
...
\zimath{明}                  % the usual equation
\zimath[pict]{明}            % the grid with the picture row
\zimath[pict,lang=zh]{明}    % meanings in Chinese
\zimath[pict=obs]{明}        % the set of pictures named obs (e.g. oracle bone glyphs)
```

```bash
zitex render -i chars.yaml --scan main.tex -x lexicon.yaml -l en -l zh
xelatex main.tex
```

`--scan` writes the snippets and `zitex-out/picts/`. A complete example is in `examples/pict/`.

### 3.2 Lexicon

```yaml
日: {pinyin: rì,   gloss: {en: sun,    zh: 太阳}, pict: "☀️"}
月: {pinyin: yuè,  gloss: {en: moon,   zh: 月亮}, pict: "🌙"}
明: {pinyin: míng, gloss: {en: bright, zh: 明亮}, concept: BRIGHT, category: LIGHT, pict: sun-moon.png}
```

Keys: `pinyin`, `gloss` (per language), `concept`, `category`, `pict`, and `pict_<set>` for a named set. Merging several lexicon files works as before: later files override earlier ones.

### 3.3 Oracle bone glyphs from Orascope

`python scripts/export_picts.py --dest ../zinets-latex/data/ele_chars` (run in the Orascope repo) writes one ★-picked glyph per elemental character as `u<hex>.png`, a `picts.csv` that records where each came from, and a `lexicon.yaml` with pinyin, gloss, concept, category and pict. On 2026-10-11 it wrote 51 glyphs and 306 lexicon entries; 255 elemental characters with oracle bone forms still have no ★ pick, so they fall back to an emoji or to nothing. Then:

```bash
ZITEX_PICT_DIR=data/ele_chars zitex render -i chars.yaml --scan main.tex -x data/ele_chars/lexicon.yaml
```

`--chars 日月明虫工虹 --set obs` exports just those characters (they need not be elemental) and writes the lexicon as `pict_obs` keys only, so it can be merged after a lexicon that has the glosses. `examples/pict/obs/` was made this way: `main.tex` shows the same equations with emoji (default set) and with these glyphs (`pict=obs`).

The glyphs come from HUST-OBC (CC BY-NC 4.0): keep the attribution.

### 3.4 Settings

| Variable | Default | Meaning |
|---|---|---|
| `ZITEX_PICT_DIR` | none | folder searched for `u<hex>.png` etc. |
| `ZITEX_PICT_HEIGHT` | `1.8em` | height of every pict |
| `ZITEX_PICT_WIDTH` | `1.8em` | width of every pict (the picture is scaled to fit) |
| `ZITEX_MEANING_WIDTH` | `6em` | meanings wrap at this width |
| `ZITEX_MEANING_SENSES` | `3` | how many `/`-separated senses show (`0` = all) |
| `ZITEX_EMOJI_FONT` | Noto Color Emoji | font used to draw an emoji pict |

### 3.5 From Python

```python
from zitex import load_yaml, load_lexicon, render_snippet
from zitex.render import math_chars

entries = load_yaml("chars.yaml")
lex = load_lexicon(entries, "lexicon.yaml")
snippet = render_snippet(entries[0], "pictmath", lex=lex, lang="zh")
lex.stage_picts(math_chars(entries[0]), "zitex-out")      # copies or draws the pictures the snippet names
```

## 4. Files

| File | Change |
|---|---|
| `src/zitex/render.py` | `render_pictmath`, `math_chars`, `pict_prelude`, `split_style`, `_arrow` (shared with `render_math`), `DEFAULT_STYLES`, `LANG_STYLES` |
| `src/zitex/lexicon.py` | `concept`, `category`, `pict` fields; `get_meaning`, `get_pict`, `pict_name`, `stage_picts`; emoji drawing |
| `src/zitex/config.py` | new: `.env` and environment settings |
| `src/zitex/build.py` | `pictmath` in `LANG_STYLES`, `scan_tex` reads `pict`, staging, `picts` in the manifest |
| `src/zitex/cli.py`, `pipeline.py` | the style name, staging for single output and preview |
| `src/zitex/zitex.sty` | the `pict` key |
| `tests/test_pict.py` | 20 tests: meaning and pict rules, grid rows, nested brackets, `.env`, scan, staging, named sets, real XeLaTeX compiles |
| `examples/pict/`, `.env.example`, `data/ele_chars/` | example, settings template, exported glyphs |

## 5. Limits and open items

- **Not MathJax.** A snippet that uses picts needs XeLaTeX with `graphicx`. The text-only `math` style is unchanged and still works in MathJax.
- **Width.** A long equation with long meanings can overflow a page. Lower `ZITEX_MEANING_WIDTH` or `ZITEX_MEANING_SENSES`; there is no automatic scaling.
- **stdout.** `zitex render … -o -` prints the snippet but cannot stage the pictures it names.
- **Calligraphy** (the author's next idea): a named set (`pict_calli`, `\zimath[pict=calli]`) already fits it, as another folder of pictures. A second picture *row* for it is not built.
- **Concept in the picture row.** Today `concept` and `category` only appear as a fallback meaning. A row of their own is possible.
- **Tests.** 20 new tests pass. The full suite has 6 failures that were there before this change (`test_pipeline.py` and `test_ui.py`: `extract` and the generate page), unrelated to it.
