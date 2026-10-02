# ZiNets-LaTeX Spec

Status: implemented, partly reviewed by the author. Test data: `tests/data/chars.yaml` (29 characters). Positions and patterns follow `docs/DEV/claude/zi-matrix.md`.

## Terminology

A character has three dimensions. zitex uses the everyday word for each, and keeps the formal term for reference:

| Dimension | Everyday term | Formal term | In the data |
|---|---|---|---|
| form | **shape** (形) | IDS, Ideographic Description Sequence (Unicode) | `shape` |
| sound | **sound** (音) | pinyin | `pinyin` |
| meaning | **meaning** (義) | semantics | `meaning` |

**Why "shape".** It points at how a character is written: the strokes and the order of hand movements, which matters for handwriting and calligraphy. "IDS" says only that the string is a description of an ideograph. A shape string uses the Unicode IDS operators (⿰ ⿱ ...) plus ZiNets additions for flat patterns (`∴ ∵ ∷ ⁙`), so it stays readable by tools that know IDS. The word "IDS" is still used where the Unicode standard itself is meant.

The old field name `ids` is no longer accepted (zitex has not been released, so there was nothing to keep compatible).

## 1. Tree model

A decomposition is a tree.

- **Leaf:** `{c: <component>, pos: <position>}`
- **Branch:** `{op: <operator>, pos: <position>, parts: [<node>, ...]}`
- **Named branch:** a branch may also carry `c`, the composite it forms. Example: `{c: 喿, op: ⿱, pos: M, parts: [...]}`. This keeps intermediate components such as 喿 or 品 addressable. Without `c` the branch is anonymous.
- The root is a branch (or a single leaf) and has no `pos`.
- `pos` is stored on every non-root node, **per level**: it is relative to the node's parent, as in the SQLite DB.
- How deep to decompose is an authoring choice. A character like 寺 can be a leaf in 時 and have its own entry elsewhere.
- A branch has a computed **pattern**: the positions of its children joined by hyphens, such as `L-M` or `U-LD-RD` (`Node.pattern`).

A character entry:

```yaml
- char: 時
  pinyin: shí            # optional
  meaning: time          # optional
  shape: "⿰日寺"         # compact form, must match the tree
  tree: {op: ⿰, parts: [{c: 日, pos: L}, {c: 寺, pos: M}]}
  role: {日: semantic, 寺: phonetic}   # optional
  note: ...              # optional
  decision: ...          # optional: a choice made by the author
  review: ...            # optional: marks an uncertain decomposition
```

`role` values: `semantic`, `phonetic`, `force` (a force carrier in the paper's sense). A value can also be a list, for a component that plays two roles (`工: [semantic, phonetic]`).

### Readings

How the components of a character work (which is meaning, which is sound) is an **interpretation**, and for some characters the dictionary tradition and the author disagree. An entry can carry several named **readings**:

```yaml
- char: 虹
  readings:
    - name: author            # the first reading is the default
      role: {虫: semantic, 工: semantic}
      note: Meaning first. ...
    - name: dictionary
      source: Shuowen, 从虫，工聲 (quoted from memory)
      role: {虫: semantic, 工: phonetic}
```

- `role:` directly on an entry is a shorthand for one reading named `default`. If an entry has both `role` and `readings`, `role` comes first.
- Readings change how roles are shown, and nothing else: piece colours in the tree and the matrix, and the arrow label of the `math` style under `arrow="role"` (`sound: gōng`). The structure and the positions do not depend on the reading.
- A reading is chosen with `reading=` (`render_snippet(..., reading="dictionary")`, `zitex render --reading`, `\zi[reading=...]`). A character without that reading uses its default, so one reading can be requested for a whole file.
- Snippet names get `@reading` when a reading was asked for: `虹-math-en@dictionary.tex`.

## 2. Positions and patterns

The 11 Zi-Matrix labels, canonical in data and code. The Chinese names are accepted on input and converted when a file is loaded.

| Code | Name | Chinese |
|---|---|---|
| L | Left | 左 |
| R | Right | 右 |
| M | Mid, the center of gravity | 中 |
| U | Up | 上 |
| D | Down | 下 |
| Mi | Mid-inner (reserved) | 中内 |
| Mo | Mid-outer, the enclosing frame | 中外 |
| LU | Left-Up | 左上 |
| LD | Left-Down | 左下 |
| RU | Right-Up | 右上 |
| RD | Right-Down | 右下 |

`M` is the component that holds the character's center of gravity: the geometric middle in `L-M-R`, `U-M-D` and inside a frame, and otherwise the non-radical part. **A Kangxi radical is peripheral**: in 佛 the radical 亻 is `L` and 弗 is `M`. Two radicals, or none, are peers (`L-R`, `U-D`). The full rationale, the frequencies from Figure 5 of the paper, and the open points are in `docs/DEV/claude/zi-matrix.md`.

## 3. Operators

The Unicode IDS operators plus ZiNets operators for flat patterns. Each operator allows one or more patterns (the first is the default; for ⿰ and ⿱ the default follows the radical rule).

| Op | Name | Allowed patterns |
|---|---|---|
| ⿰ | left–right | `L-M` `M-R` `L-R` |
| ⿱ | top–bottom | `U-M` `M-D` `U-D` |
| ⿲ | left–middle–right | `L-M-R` |
| ⿳ | top–middle–bottom | `U-M-D` |
| ⿴ | full surround | `Mo-M` |
| ⿵ | surround from above | `Mo-D` |
| ⿶ | surround from below | `Mo-U` |
| ⿷ | surround from left | `Mo-R` |
| ⿸ | surround from upper left | `LU-M` |
| ⿹ | surround from upper right | `RU-M` (no data in the paper) |
| ⿺ | surround from lower left | `LD-M` |
| ⿻ | overlaid | `M-M` (not defined in the paper) |
| **∴** | **triangle, apex up** | `U-LD-RD`, also `U-L-R` |
| **∵** | **triangle, apex down** | `LU-RU-D` |
| **∷** | **2×2 grid** | `LU-RU-LD-RD` |
| **⁙** | **four corners and a center** | `LU-RU-M-LD-RD` |
| **<pattern>** | **general form** | exactly that pattern |

### The ZiNets operators

IDS has no operator for a level with three, four or five immediate components arranged flat. The usual workaround nests (`⿱口⿰口口`), which invents intermediate nodes that have no meaning. The Zi-Matrix expresses such a level directly, so shape strings need an operator for it:

```
∴ A B C        A on top, B bottom-left, C bottom-right           品 = ∴口口口   叒 = ∴又又又
∵ A B C        A top-left, B top-right, C at the bottom          哭 = ∵口口犬
∷ A B C D      top-left, top-right, bottom-left, bottom-right    叕 = ∷又又又又
⁙ A B C D E    top-left, top-right, center, bottom-left, bottom-right    器 = ⁙口口犬口口
<L-RU-RD> A B C   any pattern: the labels are the pattern, one part per label
```

- `∴ ∵ ∷` are U+2234, U+2235, U+2237. `⁙` is U+2059, which Noto Serif CJK SC lacks, so it is an input symbol only: a tree prints the pattern instead.
- Arity is fixed by the operator, so prefix parsing stays unambiguous.
- The general form covers every pattern, including ones the data has not used yet, such as `LU-LD-R` and `L-RU-RD` (no symbol has been chosen for those).
- Labels in a pattern are written in reading order: along the main axis of the layout, top to bottom for a vertical layout and left to right for a horizontal one, with a frame (`Mo`) first.
- **Export to plain IDS:** a flat operator can be lowered to nested IDS (`∴ABC` to `⿱A⿰BC`) for tools that only know standard IDS. The reverse is not automatic.

### Validation

Every check is a **warning**; a warning never stops a build.

| Code | Meaning |
|---|---|
| W1 | `pos` is not one of the 11 labels |
| W2 | the level's pattern is not allowed for its operator |
| W3 | a non-root node has no `pos` |
| W4 | `shape` does not match the string generated from `tree` |
| W5 | wrong number of children for the operator, or an unknown operator |
| W6 | a branch has no children |
| W7 | position regions overlap, or there is more than one `M` |
| W8 | a Kangxi radical is labelled `M` although the other part is not a radical |
| W9 | a reading gives a role to a component that is not in the tree |
| W10 | a reading uses an unknown role (known: `semantic`, `phonetic`, `force`) |
| W11 | two readings of one character have the same name |

W7 uses a 3×3 grid: `L` and `R` claim a column, `U` and `D` a row, `LU RU LD RD` a corner cell, and `M` is whatever the others leave. `U`, `D`, `L` and `R` mean only the middle cell of their edge when a corner label shares it (`LU-U-RU`), or, for `L` and `R`, when `M` or both `U` and `D` are present (`U-L-M-D`). `U-L-R` overlaps at the corners, so it is reported with a hint to use `U-LD-RD`. Enclosure patterns (`Mo-X`) and `⿻` are exempt.

## 4. Compact `shape` grammar

```
expr    := leaf | named | op expr{arity(op)}
leaf    := any single non-operator character (a Unicode code point) | "{" name "}"
named   := leaf "(" expr ")"          # a composite given a name: 喿(⿱品(∴口口口)木)
op      := ⿰ ⿱ ⿲ ⿳ ⿴ ⿵ ⿶ ⿷ ⿸ ⿹ ⿺ ⿻ ∴ ∵ ∷ ⁙ | "<" pattern ">"
pattern := label ("-" label)*
```

- Prefix form, no brackets around an operator's arguments.
- A shape string carries no positions. They are filled in from the operator's default pattern, and for ⿰ and ⿱ from the radical rule. Positions that differ from this are written in the YAML `tree`.
- A component with no code point (rare elemental characters) is written `{name}`, for example `⿰日{demo}`, and stored as `c: demo`. Any `c` longer than one character is such a name. It can also name a composite: `{wide}(⿱一二)`. How it is drawn is set in `fonts.yaml` (see section 6).

## 5. Test set coverage

| Feature | Characters |
|---|---|
| ⿰ with a radical (`L-M`) | 時, 悔, 作, 佛 |
| ⿰ peers (`L-R`) | 双 |
| ⿱ | 寺, 巠 |
| nested ⿱⿰ | 想 |
| ⿲ | 衍 |
| ⿳ + ⿻ | 愛 |
| ⿴ ⿵ ⿷ | 國, 同, 区 |
| ⿸ ⿹ ⿺ | 病, 句, 近 |
| ∴ | 品, 森, 晶, 淼, 众, 叒 |
| ∵ | 哭 |
| ∷ | 叕 |
| ⁙ (five parts) | 器 |
| deep nesting, named nodes | 藻 (喿 and 品 named, ∴ inside) |
| paper examples | 禺, 巠, 寺, 氢, 時, 乍 (in 作) |
| two readings | 虹 (author, dictionary) |

## 6. Fonts and fallback (M4)

`fonts.yaml` (all keys optional):

```yaml
primary: Noto Serif CJK SC
fallbacks: [AR PL UMing CN]          # tried in order when the primary font lacks a glyph
components:
  "{demo}": {svg: glyphs/demo.svg}   # image for a component with no code point (needs inkscape)
  𠀉: {font: Some Font}              # force a font for one component
  甲: {alias: 日}                     # draw another character instead
```

Resolution for each component: override, then primary font, then fallbacks, then a boxed label (`U+20009` or the name), reported as missing. Coverage is read from the font files with fontTools. A font that cannot be inspected is assumed to cover everything, so a build never fails on a guess.

Commands: `zitex fonts -i data.yaml --fonts fonts.yaml [--strict]` prints the report, and `zitex render ... --fonts fonts.yaml` applies it. Snippets that use a fallback begin with `\providecommand` lines for `\zifont`, `\zisvg` and `\zimissing`, so they stay self-contained. SVG glyphs are converted to `zitex-out/glyphs/*.pdf`.

On this machine all 60 components of the original 23-character test set are in Noto Serif CJK SC. No installed font has U+20009, which makes it a good test of the missing path.

## 7. Review decisions (author)

`chars.yaml` has been reviewed. Decisions are recorded as `decision:` fields:

- **禺:** 甲 (top) + 禸 (bottom), read as interlocking / coupling.
- **藻:** 喿 (U+55BF) is kept as a named node. An earlier decision to skip it was reversed. 品 is named too.
- **愛:** keep the traditional form, because its 心 is semantically meaningful.
- **氢:** 巠 stays one unit. It carries the sense of 轻 (light), so hydrogen is the lightest element.

- **作 / 乍:** 作 = 亻 (L) + 乍 (M). 乍 stays a leaf, as an elemental component.
- **佛:** 亻 (L) + 弗 (M), preferred to 弗 as R.
- **器:** four 口 around 犬, one level with five parts: `LU-RU-M-LD-RD`.
- **句:** ⿹ with `RU-M`, confirmed. It is the only `RU-M` case in the test data.
