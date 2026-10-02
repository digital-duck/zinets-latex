# Zi-Matrix Positional Notation, and its Mapping to IDS (draft 3)

Source: Figure 5 of the paper (Gong, arXiv:2502.19428), "Distribution of elemental character compositional patterns", plus the author's definitions and corrections. Status: **draft 3, implemented and reviewed by the author ("looking good")** in zitex on 2026-10-01 after the author's second round of answers. Anything still unconfirmed is marked **(proposal)** or **(open)** and collected in section 8. The implemented form is in `spec.md`; the code is `src/zitex/ops.py`, `radicals.py` and `validate.py`.

## 1. Why formalize now

zitex stores a position (`pos`) on every component and checks it against the shape string. Today the positions are Chinese labels and the check assumes the position follows from the operator alone. The notation does not work that way (section 3), and fixing it before release avoids a data migration later.

## 2. The 11 labels

| Code | Name | Chinese | Meaning |
|---|---|---|---|
| L | Left | 左 | left part |
| R | Right | 右 | right part |
| M | Mid | 中 | the **center of gravity** of the character (see 3.2) |
| U | Up | 上 | upper part |
| D | Down | 下 | lower part |
| Mi | Mid-inner | 中内 | reserved. Only the `M-Mi` cases (118) still use it, and the author will review them. `Mi-Mo` is not used (use `Mo-M`) |
| Mo | Mid-outer | 中外 | the enclosing frame (confirmed: `Mo` is for enclosures and frames) |
| LU | Left-Up | 左上 | upper-left corner |
| LD | Left-Down | 左下 | lower-left corner |
| RU | Right-Up | 右上 | upper-right corner |
| RD | Right-Down | 右下 | lower-right corner |

The codes are canonical in data and code (ASCII, short, easy to type). The Chinese names are display aliases and are also accepted on input.

## 3. How the notation works

### 3.1 A pattern describes one level, and the tree is nested

A **compositional pattern** is the list of positions of the *immediate* components of a character, joined by hyphens: `L-M`, `U-LD-RD`. A deeper character has one pattern per level, and positions are stored **per level**, relative to the parent. This is what zitex's tree already does, and it is how the SQLite DB stores them.

For example, if 澡 is kept as a node: 藻 is `U-M` (艹, 澡), 澡 is `L-M` (氵, 喿), 喿 is `U-D` (品, 木), and 品 is `U-LD-RD`. (`tests/data/chars.yaml` skips the 澡 level.)

Figure 5 counts the patterns over about 6,000 characters (the frequencies sum to 6,015).

### 3.2 `M` is the center of gravity

> `M` is the component that holds the character's **center of gravity**. That is often the **geometric middle**, and also, in most two-part characters, the non-radical part.

Two things follow:

- **Geometric.** In `L-M-R` and `U-M-D` the `M` part is literally in the middle. In `⿴` the inner part is in the middle.
- **Radical rule.** When a **Kangxi radical** is involved, the radical is *peripheral* and gets a peripheral label (L, R, U, D, LU, LD, ...). The other component is `M`. So `佛 = 亻(L) + 弗(M)`, `時 = 日(L) + 寺(M)`, `藻 = 艹(U) + 澡(M)`, and not `(L, R)`. When neither part is a radical (or both are), the parts are peers: `L-R`, `U-D`.

The radical rule can be **computed**, which is a useful consequence: given the list of Kangxi radicals, the label `M` can be assigned automatically, and a hand-written label can be checked against it. The 214 Kangxi radicals can be generated from Unicode (`NFKC` of U+2F00 to U+2FD5 gives exactly 214 characters, such as 日 and 心). Their variant forms (亻 氵 忄 艹 辶 刂 and so on) are not covered by that, so the list needs those added by hand.

This is implemented in `src/zitex/radicals.py` (214 radicals from Unicode, about 35 hand-listed variants, and the CJK Radicals Supplement block). A dry run on the 12 two-part levels of the test set gives:

| Level | Radical parts | Rule says |
|---|---|---|
| 時 日 + 寺, 作 亻 + 乍, 悔 忄 + 每 | one | `L-M` ✓ |
| 藻 艹 + 澡 | one | `U-M` ✓ |
| 想 相 + 心 | one (心) | `M-D` |
| 喿 品 + 木 | one (木) | `M-D` |
| 禺 甲 + 禸 | one (禸) | `M-D` |
| 寺 土 + 寸, 巠 巛 + 工, 同 一 + 口, 想 木 + 目 | both | peers (`U-D`, `L-R`) |

The first four match what the author gave. The `M-D` rows and the peers rows are rule outputs for the author to confirm.

The rule is a tendency and not a law. In `近 = 辶 + 斤` both parts are radicals, and the data still has `LD-M`. So the validator should **warn**, not reject.

## 4. Figure 5 patterns, with the IDS operator and the zitex operator

| # | Pattern | Count | Share | IDS operator | Note |
|---|---|---|---|---|---|
| 0 | `L-M` | 3033 | 50.4% | ⿰ | 佛 = 亻 + 弗 |
| 1 | `U-D` | 727 | 12.1% | ⿱ | peers, e.g. 卡 = 上 + 下|
| 2 | `U-M` | 688 | 11.4% | ⿱ | 藻 = 艹 + 澡 |
| 3 | `L-R` | 534 | 8.9% | ⿰ | peers, e.g. 双 = 又 + 又 |
| 4 | `M-R` | 301 | 5.0% | ⿰ | radical on the right, e.g. 刮 = 舌 + 刂 |
| 5 | `U-M-D` | 139 | 2.3% | ⿳ | e.g. 莫 =	艹 + 日	+ 大 |
| 6 | `LD-M` | 120 | 2.0% | ⿺ | 近 = 辶 + 斤 |
| 7 | `M-Mi` | 118 | 2.0% | ⿵ ⿶ ⿷ ? | **to be reviewed by the author**, see 5.3 |
| 8 | `LU-M` | 106 | 1.8% | ⿸ | 病 = 疒 + 丙 |
| 9 | `M-D` | 70 | 1.2% | ⿱ | radical at the bottom, e.g. 想 = 相 + 心 |
| 10 | `LU-RU-D` | 45 | 0.7% | none (needs nesting) | 哭 = 口 口 / 犬. zitex `∵`. Written `D-LU-RU` in Figure 5; the author renamed it |
| 11 | `LU-LD-R` | 28 | 0.5% | none (needs nesting) | two on the left, one on the right |
| 12 | `L-M-R` | 26 | 0.4% | ⿲ | e.g. 衍 = 彳 + 氵+ 亍|
| 13 | `U-LD-RD` | 21 | 0.3% | none (needs nesting) | 品 = 口 / 口 口, 叒 = 又 / 又 又. zitex `∴` |
| 14 | `Mo-M` | 21 | 0.3% | ⿴ | written `M-Mo` in Figure 5; the author replaced it with `Mo-M`, e.g. 回 = 口 + 口 |
| 15 | `L-RU-RD` | 18 | 0.3% | none (needs nesting) | one on the left, two on the right |
| 16 | `U-L-R` | 8 | 0.1% | same as `U-LD-RD` | same topology as `∴`, see 5.2 |
| 17 | ~~`Mi-Mo`~~ | 6 | 0.1% | | not used. The author uses `Mo-M` instead |
| 18 | `LU-RU-LD-RD` | 6 | 0.1% | none (needs nesting) | 叕 = 又 × 4 |

Observations:

- **No `RU-M` pattern in Figure 5.** ⿹ has no counterpart there. The author confirmed that 句 stays ⿹ with `RU-M`, so `RU-M` is kept as an allowed pattern even though Figure 5 has no case of it.
- **Four of the flat patterns are triangles** (`LU-RU-D`, `U-LD-RD`, `LU-LD-R`, `L-RU-RD`), and one is a 2×2 grid. IDS has no single operator for any of them. Because the data is hierarchical with positions per level, a three-part level has three immediate components and no intermediate node, so a nested `⿱A⿰BC` would invent a node that does not exist (see 6).

## 5. Mapping IDS and positions

### 5.1 Granularity

The two notations answer different questions, and neither contains the other.

| What is recorded | Zi-Matrix positions | IDS |
|---|---|---|
| Center of gravity / which part is `M` | **yes** | no |
| Peers versus radical + body (`L-R` vs `L-M`) | **yes** | no |
| 3 or 4 parts at one level, without inventing a nesting | **yes** | no |
| Enclosure direction | **yes**, through the pairing in 5.3 | yes |
| Overlay (⿻) | no | **yes** |

A full record carries both, and the validator checks that they agree.

### 5.2 Operator to allowed patterns

| Operator | Pattern | Status |
|---|---|---|
| ⿰ | `L-M` `M-R` `L-R` | Figure 5 |
| ⿱ | `U-M` `M-D` `U-D` | Figure 5 |
| ⿲ | `L-M-R` | Figure 5 |
| ⿳ | `U-M-D` | Figure 5 |
| ⿸ | `LU-M` | Figure 5 |
| ⿹ | `RU-M` | no data |
| ⿺ | `LD-M` | Figure 5 |
| **⿴** | **`Mo-M`** | the author's mapping |
| **⿵** | **`Mo-D`** | the author's mapping |
| **⿶** | **`Mo-U`** | the author's mapping |
| **⿷** | **`Mo-R`** | the author's mapping |
| ⿻ | none | not in the paper |
| `∴` | `U-LD-RD`, also the alias `U-L-R` | zitex extension |
| `∵` | `LU-RU-D` | zitex extension |
| `∷` | `LU-RU-LD-RD` | accepted by the author. U+2237 PROPORTION, four dots in a square. In Noto Serif CJK |

`U-L-R` (8 characters) has the same topology as `U-LD-RD` and maps to `∴`. It is treated as an **alias**: accepted on input, normalized to `U-LD-RD`, with a warning so the data can be cleaned up.

### 5.3 Enclosures

The author's mapping: the frame is `Mo`, and the second label says **where the inner part sits inside the frame**.

| IDS | Pattern | Reading |
|---|---|---|
| ⿴ | `Mo-M` | frame all around, inner part in the middle |
| ⿵ | `Mo-D` | frame open at the bottom, inner part at the bottom |
| ⿶ | `Mo-U` | frame open at the top, inner part at the top |
| ⿷ | `Mo-R` | frame open to the right, inner part at the right |

This is more informative than Figure 5, which has only `M-Mi`, `M-Mo` and `Mi-Mo`. It also means the pattern now determines the operator, so there is no ambiguity in the reverse mapping.

Decisions:

- `Mi-Mo` is dropped, and `M-Mo` becomes `Mo-M`.
- `Mo` is for enclosures and frames. The corner enclosures keep their own style: ⿸ is `LU-M`, ⿺ is `LD-M`, with the frame labelled by its corner and the inner part `M`.
- The 118 `M-Mi` cases are left for the author to review. They will probably be re-labelled `Mo-D`, `Mo-U` or `Mo-R` according to their direction.

### 5.4 Reverse mapping (pattern to operator)

Every pattern in 5.2 has exactly one operator. The triangle and grid patterns map to the zitex operators `∴ ∵ ∷`, and `LU-LD-R` and `L-RU-RD` are the two that still need one (see 6).

## 6. Flat patterns, repeated components and patterns beyond Figure 5

Characters made of one component repeated: 双 = 又 + 又 (`L-R`), 叒 = 又 × 3 (`U-LD-RD`), 叕 = 又 × 4 (`LU-RU-LD-RD`), 品 = 口 × 3, 森 = 木 × 3. Each repeat is a separate part, and the math renderer's `collapse` option prints `4 × 又`.

### 6.1 Why the notation is not limited to Figure 5

The author's SQLite DB decomposes **器 = 口 (LU) + 口 (RU) + 犬 (M) + 口 (LD) + 口 (RD)**: four pits around a dog, the primitive trap (4 × 口 + 犬). That is one level with **five** immediate components, and the pattern `LU-RU-M-LD-RD` is not in Figure 5. IDS can only reach it by nesting (`⿳⿰口口犬⿰口口`), which invents two intermediate pair nodes that have no meaning. This is the main reason for the notation, and it means the set of patterns is **open-ended**: any combination of labels that does not overlap is a valid pattern.

### 6.2 Operators for flat patterns

| Pattern | Operator |
|---|---|
| `U-LD-RD` | `∴` |
| `LU-RU-D` | `∵` |
| `LU-RU-LD-RD` | `∷` |
| `LU-RU-M-LD-RD` | `⁙` U+2059 FIVE DOT PUNCTUATION: four corners and a center **(proposal)**. Not in Noto Serif CJK SC, so it needs a fallback font if it is ever printed. In shape strings it is only input |
| `LU-LD-R`, `L-RU-RD` | no symbol chosen |
| any other | the general form below |

**General form (proposal).** Write the pattern itself as the operator: `<LU-RU-M-LD-RD>口口犬口口`. It covers every pattern, including ones the data has not used yet. The one-character operators are shortcuts for the common ones, and the renderers print the pattern name when a symbol has no glyph.

### 6.3 Order of labels in a pattern

The author's examples (`LU-RU-D`, not `D-LU-RU`; `LU-LD-R` kept) fit one reading order **(inferred)**:

> Follow the main axis of the layout. For a vertical layout, go top to bottom, left before right within a row (`LU-RU-D`, `U-LD-RD`, `LU-RU-LD-RD`). For a horizontal layout, go left to right, top before bottom within a column (`LU-LD-R`, `L-RU-RD`). A frame comes first (`Mo-D`).

Children in the shape string and in the YAML follow the same order, so the pattern is just their labels joined.

### 6.4 A region rule for validation **(proposal)**

Each label claims cells of a 3×3 grid (with one refinement made when the database was read: `U D L R` mean the middle cell of their edge when a corner label, or an `M`, sits beside them, see `spec.md`): `L` the left column, `R` the right column, `U` the top row, `D` the bottom row, `LU` `RU` `LD` `RD` the corner cells, and `M` **whatever the others leave**, which is the central mass. A pattern is valid when its peripheral labels do not overlap, and `M` appears at most once. This accepts `L-M` (`M` is the middle and right columns), `L-M-R`, `U-M-D`, `LU-RU-M-LD-RD` and `LU-RU-D`, and it rejects `U-L-R` because `U` overlaps `L` and `R` at the corners, which agrees with treating it as an alias of `U-LD-RD`. Enclosures (`Mo-X`) are checked separately: `Mo` is the frame and `X` is where the inner part sits in it.

## 7. What this means for zitex (done)

Implemented as follows:

1. **Labels.** `POSITIONS` becomes `L R M U D Mi Mo LU LD RU RD`. The Chinese names are accepted as input aliases. The test data is converted.
2. **`OPS`.** Each operator lists its allowed pattern(s) (5.2) instead of one default position per child. A shape string that gives no positions gets the pattern's labels.
3. **`M` by rule.** The Kangxi radical list now exists (`src/zitex/radicals.py`), so `M` and the peripheral labels can be assigned automatically for two-part levels, and checked on stored data.
4. **Validator.** W2 becomes "pattern not allowed for this operator". New warnings: a pattern not in the 19 of Figure 5, the alias `U-L-R`, and `M` placement that disagrees with the radical rule.
5. **`pattern` property.** A branch gets a computed `pattern` (`"L-M"`). The Figure 5 statistics become a one-line query over the data, and `pattern` is the natural key for the SQLite bridge, since the DB stores positions per level.
6. **Operators.** `∴` and `∵` kept, `∷` added, and the general `<pattern>` form for everything else.
7. **Renderers.** Tree and `show_pos` print the new codes. The matrix needs the enclosure geometry for `Mo-U`, `Mo-D`, `Mo-R`, `Mo-M` (it already draws these four from the IDS operator).
8. **Tests and docs.** `spec.md`, the tutorial, `CLAUDE.md` and the test data change to the new labels.

## 8. Open questions

Resolved: enclosure mapping, `Mi-Mo` and `M-Mo`, `Mo` meaning, `LU-RU-D`, `∷`, positions per level, generating the radical list.

1. **The general `<pattern>` form** for flat patterns beyond `∴ ∵ ∷` (6.2). Acceptable? And is `⁙` a good symbol for `LU-RU-M-LD-RD`?
2. **The region rule** (6.4) for validating patterns, and the reading order in 6.3. Right?
3. **The `M-D` and peers rows** of the dry run (3.2): 想, 喿, 禺 as `M-D`, and 寺, 巠, 同 as peers. Do these match your DB?
4. **`M-Mi`** (118): your review will decide whether they become `Mo-D`, `Mo-U` or `Mo-R`.
5. ~~**句:**~~ resolved: ⿹ with `RU-M`.
6. **`U-L-R`:** alias of `U-LD-RD`, normalized with a warning?
