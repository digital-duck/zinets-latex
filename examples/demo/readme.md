# zitex demo

A one-page document that uses zitex: equations with pinyin and glosses, Zi-Matrix boxes, a decomposition tree and an inline formula. It is built in two steps. `zitex render` turns decompositions into LaTeX snippets, and `xelatex` typesets the document, which pulls those snippets in with `\zimath`, `\zimatrix` and so on.

## Before you start

You need these once.

1. **The `zitex` command.** From the repository root, in the `zinets2` environment:
   ```bash
   conda activate zinets2
   pip install -e .
   zitex --version
   ```
2. **XeLaTeX** with the `tikz`, `xeCJK`, `fontspec` and `amsmath` packages, and the Noto Serif CJK SC font. Check with `xelatex --version` and `fc-list | grep "Noto Serif CJK SC"`.
3. **`zitex.sty` where XeLaTeX can find it.** Install it into your personal TeX folder:
   ```bash
   zitex install-sty
   ```
   It prints where it put the file and `TeX finds it at ...`. Run it again after you upgrade zitex.

## Run it

All commands run from this folder.

```bash
cd examples/demo

zitex render -i ../../tests/data/chars.yaml --scan main.tex -x ../../tests/data/lexicon.yaml -l en -l fr --collapse --arrow role

xelatex main.tex
```

The result is `main.pdf` in this folder.

What the first command does:

| Part | Meaning |
|---|---|
| `-i ../../tests/data/chars.yaml` | the decompositions (shape, pinyin, meaning, roles) |
| `--scan main.tex` | render only what `main.tex` asks for, as snippets (`.tex` files) into `zitex-out/` |
| `-x ../../tests/data/lexicon.yaml` | pinyin and glosses for the components, in English and French |
| `-l en -l fr` | render glosses in both languages (`\zimath[lang=fr]{悔}` needs French) |
| `--collapse` | write `3 × 木 = 森` and not `木 + 木 + 木 = 森` |
| `--arrow role` | label the arrow with the phonetic part when a character has one (`—(sound: sì)→`) |

It writes 9 snippets and a `build_manifest.json` into `zitex-out/`:

```
u54ed-哭-matrix.tex   u570b-國-matrix.tex   u6094-悔-math-fr.tex   u611b-愛-tree.tex   u6642-時-math-en.tex
u68ee-森-math-en.tex  u6c22-氢-formula-en.tex  u85fb-藻-math-en.tex  u85fb-藻-matrix.tex
```

A snippet's name is `u<hex>-<char>-<style>[-<language>].tex`, the character's code point in hex and then the character itself (藻 is `u85fb-藻`), and `zitex.sty` looks for exactly that name. `zitex-out/build_manifest.json` maps the names back to the characters.

## The shortcut

```bash
make          # runs both commands, finding zitex.sty through TEXINPUTS (no install needed)
make clean    # removes zitex-out/, main.pdf and the LaTeX auxiliary files
```

## What you should see

Under **Equation (English)**, three equations: 時 with an arrow labelled `sound: sì`, 森 as `3 × 木 = 森`, and 藻 with a bracketed group. Under **Equation (French)**, 悔 with glosses in French (`cœur`, `chaque`). Then three matrices (國, 哭, 藻), a tree for 愛, and the inline formula for 氢. If you see red `[字?]` marks instead, see below.

## What `main.tex` uses

| Command | Result |
|---|---|
| `\zimath{時}` | the equation, in the default language (English) |
| `\zimath[lang=fr]{悔}` | the same, with French glosses |
| `\zimatrix{國}` | nested boxes laid out by the structure |
| `\zitree{愛}` | the decomposition tree |
| `\ziformula{氢}` | one line: `气 + 巠 → 氢 (qīng, hydrogen)` |

Change a character in `main.tex` and run the two commands again. A character that is not in `chars.yaml` is shown as a red `[字?]`.

## If something goes wrong

| Symptom | Cause and fix |
|---|---|
| `zitex: command not found` | activate the environment (`conda activate zinets2`) and run `pip install -e .` in the repository root |
| `File 'zitex.sty' not found` | run `zitex install-sty`, or use `make` |
| red `[字?]` marks, and `Missing zitex-out/...` in `main.log` | the snippets are not where LaTeX looks. Run `zitex render` in the **same folder** as `main.tex` (the `zitex-out/` folder is relative to where you run `xelatex`), and run it again after you add a new `\zi` command |
| `Missing character` for a Chinese character | the font is missing. Install Noto Serif CJK SC, or pick another with `\setCJKmainfont` after `\usepackage{zitex}` |
| the PDF looks out of date | `make clean`, then run it again |
