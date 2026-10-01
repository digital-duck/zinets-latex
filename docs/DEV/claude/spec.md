# ZiNets-LaTeX Spec (M0, draft)

Status: draft for review. Test data: `tests/data/chars.yaml` (23 characters).

## 1. Tree model

A decomposition is a tree.

- **Leaf:** `{c: <component>, pos: <position>}`
- **Branch:** `{op: <operator>, pos: <position>, parts: [<node>, ...]}`
- **Named branch:** a branch may also carry `c`, the composite it forms. Example: `{c: 喿, op: ⿱, pos: 右, parts: [...]}`. This keeps intermediate components such as 喿 or 品 addressable. Without `c` the branch is anonymous.
- The root is a branch (or a single leaf) and has no `pos`.
- `pos` is stored on every non-root node, as in the SQLite DB.
- How deep to decompose is an authoring choice. A character like 寺 can be a leaf in 時 and have its own entry elsewhere.

A character entry:

```yaml
- char: 時
  pinyin: shí            # optional
  meaning: time          # optional
  ids: "⿰日寺"           # compact form, must match the tree
  tree: {op: ⿰, parts: [{c: 日, pos: 左}, {c: 寺, pos: 右}]}
  role: {日: semantic, 寺: phonetic}   # optional
  note: ...              # optional
  review: ...            # optional: marks an uncertain decomposition
```

`role` values: `semantic`, `phonetic`, `force` (a force carrier in the paper's sense).

## 2. Operators

All Unicode IDS operators, plus two ZiNets extensions.

| Op | Name | Arity | Child positions (in order) |
|---|---|---|---|
| ⿰ | left–right | 2 | 左, 右 |
| ⿱ | top–bottom | 2 | 上, 下 |
| ⿲ | left–middle–right | 3 | 左, 中, 右 |
| ⿳ | top–middle–bottom | 3 | 上, 中, 下 |
| ⿴ | full surround | 2 | 中外, 中内 |
| ⿵ | surround from above | 2 | 中外, 中内 |
| ⿶ | surround from below | 2 | 中外, 中内 |
| ⿷ | surround from left | 2 | 中外, 中内 |
| ⿸ | surround from upper left | 2 | 左上, 中内 |
| ⿹ | surround from upper right | 2 | 右上, 中内 |
| ⿺ | surround from lower left | 2 | 左下, 中内 |
| ⿻ | overlaid | 2 | 中, 中 |
| **∴** | **triangle, apex up (ZiNets extension)** | 3 | 上, 左下, 右下 |
| **∵** | **triangle, apex down (ZiNets extension)** | 3 | 左上, 右上, 下 |

### The ∴ and ∵ operators

Unicode IDS has no operator for one component on top and two side by side underneath. The usual workaround is `⿱口⿰口口`, which loses the fact that 品 is a single triangular pattern. ZiNets adds a ternary operator:

```
∴ A B C      A on top (上), B bottom-left (左下), C bottom-right (右下)
```

- 品 = `∴口口口`, 森 = `∴木木木`, 晶 = `∴日日日`, 淼 = `∴水水水`, 众 = `∴人人人`
- `∴` is U+2234 (THEREFORE), chosen because its three dots form the same triangle.
- Arity is fixed at 3, so prefix parsing stays unambiguous: `⿱艹⿰氵⿱∴口口口木` has a single reading.
- **Export:** the exporter can lower `∴ABC` to `⿱A⿰BC` for tools that only know standard IDS. The reverse is not automatic, because `⿱A⿰BC` is also a legitimate plain decomposition.
- **`∵` (U+2235, BECAUSE):** the inverted pattern, with two components on top and one below.

```
∵ A B C      A top-left (左上), B top-right (右上), C bottom (下)
```

  - 哭 = `∵口口犬`
  - Like `∴`, it has fixed arity 3 and lowers to standard IDS as `⿱⿰AB C` (`⿱⿰口口犬`).

## 3. Positions

The 11 labels from the paper: 上 下 左 右 中 左上 右上 左下 右下 中内 中外.

Default positions are given per operator in the table above. They are used when the compact `ids` form is expanded. The validator checks stored `pos` values against them and **warns** on a mismatch. A warning does not stop a build.

Warnings:

| Code | Meaning |
|---|---|
| W1 | `pos` is not one of the 11 labels |
| W2 | `pos` differs from the operator default for that child index |
| W3 | non-root node has no `pos` |
| W4 | `ids` does not match the string generated from `tree` |
| W5 | wrong number of children for the operator |
| W6 | a child list is empty |

`中内` and `中外` are enclosure roles. The renderer draws the outer component as a frame and the inner one inside it. They are not grid cells.

Open point: for ⿸ ⿹ ⿺ I gave the outer component the corner label (左上 / 右上 / 左下) and the inner one 中内. The paper might use 中外 for the outer one instead. This needs your check.

## 4. Compact `ids` grammar

```
expr    := leaf | named | op expr{arity(op)}
leaf    := any single non-operator character (a Unicode code point)
named   := leaf "(" expr ")"          # a composite given a name: 喿(⿱品(∴口口口)木)
op      := ⿰ ⿱ ⿲ ⿳ ⿴ ⿵ ⿶ ⿷ ⿸ ⿹ ⿺ ⿻ ∴ ∵
```

- Prefix form, no brackets.
- A component with no code point (rare elemental characters) is written `{name}`, for example `⿰日{demo}`, and stored as `c: demo`. Any `c` longer than one character is such a name. It can also name a composite: `{wide}(⿱一二)`. How it is drawn is set in `fonts.yaml` (see section 6).

## 5. Test set coverage

| Feature | Characters |
|---|---|
| ⿰ | 時, 悔, 作 |
| ⿱ | 寺, 巠 |
| nested ⿱⿰ | 想 |
| ⿲ | 衍 |
| ⿳ + ⿻ | 愛 |
| ⿴ ⿵ ⿷ | 國, 同, 区 |
| ⿸ ⿹ ⿺ | 病, 句, 近 |
| ∴ | 品, 森, 晶, 淼, 众 |
| ∵ | 哭 |
| deep nesting, named nodes | 藻 (喿 and 品 named, ∴ inside) |
| paper examples | 禺, 巠, 寺, 氢, 時, 乍 (in 作) |

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

Commands: `zitex fonts data.yaml --fonts fonts.yaml [--strict]` prints the report, and `zitex build ... --fonts fonts.yaml` applies it. Snippets that use a fallback begin with `\providecommand` lines for `\zifont`, `\zisvg` and `\zimissing`, so they stay self-contained. SVG glyphs are converted to `zitex-out/glyphs/*.pdf`.

On this machine all 60 components of the 23-character test set are in Noto Serif CJK SC. No installed font has U+20009, which makes it a good test of the missing path.

## 7. Review decisions (author)

`chars.yaml` has been reviewed. Decisions are recorded as `decision:` fields:

- **禺:** 甲 (top) + 禸 (bottom), read as interlocking / coupling.
- **藻:** 喿 (U+55BF) is kept as a named node. An earlier decision to skip it was reversed. 品 is named too.
- **愛:** keep the traditional form, because its 心 is semantically meaningful.
- **氢:** 巠 stays one unit. It carries the sense of 轻 (light), so hydrogen is the lightest element.

- **作 / 乍:** 作 = 亻 (左) + 乍 (右). 乍 stays a leaf, as an elemental component. ⿰ has no "mid" slot, so 右 is used.

Still open:
- **句:** ⿹ with 勹 versus the more common upper-left appearance (accepted for now).
