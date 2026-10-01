# ZiNets-LaTeX: Development Plan

Package and CLI name: **zitex** (`import zitex`, `zitex check ...`), source in `src/zitex/`.

Goal: write complex Chinese character decompositions in a compact text syntax and render them through **XeLaTeX** as Zi-Matrix boxes, decomposition trees and component formulas. Persistence is **YAML** for the prototype and for exchange, because ZiNets is graph-first (section 1.1); the author's relational SQLite DB is the working store for the 5000+ character decomposition. The preprocessor is **Python**. Output is both **PDF and standalone `.tex`**.

Origin: `docs/gemini/readme.md` (review of the ZiNets paper plus a first-draft `zinets.sty`). That draft is reference material only, because it has several bugs (see "Not carried over from the Gemini draft").

## 1. Decisions

| Topic | Decision |
|---|---|
| Engine | XeLaTeX (`fontspec` + `xeCJK`), available at `/usr/bin/xelatex` |
| Preprocessing | Python 3 (parser, renderer, CLI). LaTeX holds only thin, dumb macros |
| Persistence | YAML files (`data/*.yaml`) for the prototype and for exchange, in line with the graph-first design (section 1.1). The relational SQLite DB of 5000+ characters is the author's working store for the decomposition work. It is not final and is under review, so the SQLite bridge is postponed until the prototype is accepted |
| Output | Both PDF (via XeLaTeX) and standalone `.tex` snippets for embedding in the paper |
| Default CJK font | Noto Serif CJK SC / Noto Sans CJK SC (installed). Not SimSun |
| Input core | the `shape` string: Unicode IDS operators (⿰ ⿱ ⿲ ⿳ ⿴ ⿵ ⿶ ⿷ ⿸ ⿹ ⿺ ⿻) plus ZiNets position labels |

### 1.1 Why YAML

The ZiNets project is **graph-first**: knowledge, code and computation are modelled as decomposition graphs, and those graphs are persisted as YAML. The formal statement is "Graph.yaml as Universal IR" (2026-09-27), in `/home/papagame/projects/digital-duck/zinets/RESEARCH-status-and-plan.csv` and `README-graph-vision.md`. The practice so far:

- **ConceptBook** (`conceptbook-app`) stores each concept book as a `graph.yaml` (`primitives` → `concepts` → `applications`), and the `cba` CLI turns it into pages.
- **Graph-Code** (`gfc`) reads the same format to scaffold software.
- **SPL scripts** are planned next (still a TODO in the vision doc): an `.spl` script is already a computation DAG, so persisting it as YAML makes it browsable and validatable by the same tools.
- **Origin.** `graph.yaml` itself started from ZiNets character decomposition (character → radicals → strokes). zitex brings that decomposition back to characters, typeset.

Reasons this matters for zitex:

1. **One format across tools.** A decomposition written for zitex can be read, validated and visualised by the rest of the ecosystem, and the reverse. The CSV row on the ecosystem puts it as one validator, one visualizer and one navigator for all domains.
2. **Human-readable and diffable.** The data is reviewed by hand. The test set carries `decision:` and `review:` notes next to each entry, and comments are allowed. JSON allows neither.
3. **Fits reductionism.** The elemental characters (元字) or radicals are the *primitives*. Everything else (composite characters, families, applications) is *derived* from them, which is exactly the `primitives` → `concepts` → `applications` direction of `graph.yaml`.
4. **Two stores, two jobs.** The relational SQLite DB is how the 5000+ character decomposition work is done and streamlined, so it stays the working store. YAML is good for prototyping zitex, for hand review, and for exchange with the graph tools. The bridge (M5) maps between them.

**Three dimensions, three graphs.** A character has shape, sound and meaning. The same graph-first approach applies to each:

| Dimension | Graph | Status |
|---|---|---|
| shape (form) | primitives (元字, radicals) → derived characters, drawn as a tree, matrix or equation | what zitex does today |
| sound | the same approach, later | not started |
| meaning | a semantic network of concepts: the semantic evolution of characters over the centuries | the original motivation of ZiNets (knowledge construction driven by concepts) |

So the **tree is a rendering** of the form dimension, a view and not the persistence model. The persisted model is the graph, and zitex's job is to turn it into typeset views.

Open point, to settle when M5 starts: today a zitex entry carries a tree per character (`char`, `shape`, `tree`, `role`), which is already a per-character view of the shape graph. `graph.yaml` is the shared DAG of `primitives`, `concepts` and `applications`. The two should be made compatible, or a converter written (graph in, per-character trees out), so a zitex file can be read by `cba` and `gfc`. The two schemas have not been compared in detail yet.

## 2. Architecture

```
 decomposition source              Python (src/zitex/)                    XeLaTeX
 ───────────────────      ───────────────────────────────────      ─────────────────────
 data/*.yaml         ─►   load → validate → tree (dataclass)  ─►   zitex.sty (thin macros)
 inline  \zi{...}    ─►   render: matrix | tree | formula     ─►   main.pdf
 existing net format ─►   (importer: 想(相+心))                     fonts.yaml → fallbacks
```

Two ways to use it:

1. **Batch:** `zitex render data.yaml [--scan doc.tex]` writes snippets (plain TikZ `.tex`) and figures (`.pdf`) for the characters in a YAML file, or for the `\zi{...}` calls in a paper.
2. **Library:** `zitex.render(char_or_expr, style="tree")` returns a LaTeX string, for use from the zinets app or notebooks.

Keeping the logic in Python means the `.sty` stays a small bundle of styles and wrappers, with no `\expandafter` code.

## 3. Data model (YAML)

One entry per character. **Positions are stored per component**, as in the SQLite DB, so `pos` is authored data and not derived. The tree gives the structure (operator plus nesting). The parser checks that each `pos` is consistent with its parent operator and reports a warning if not, because the DB is still being revised and may contain errors.

```yaml
# data/sample.yaml
- char: 藻
  pinyin: zǎo
  meaning: algae, aquatic plant
  shape: "⿱艹⿰氵喿"         # optional shortcut: expands to a tree with default positions
  tree:                      # canonical form: pos is stored per component
    op: ⿱
    parts:
      - {c: 艹, pos: 上}
      - op: ⿰
        pos: 下
        parts:
          - {c: 氵, pos: 左}
          - op: ⿱
            pos: 右
            parts:
              - {c: 木, pos: 上}
              - {c: 品, pos: 下}
  role:                      # optional: semantic / phonetic / force-carrier
    艹: semantic
    喿: phonetic
- char: 時
  shape: "⿰日寺"
```

- `tree` with an explicit `pos` on every component is the canonical form and the source of truth. This matches how the SQLite DB stores it, so later import and export is a direct mapping.
- `shape` is an optional shortcut for writing new entries quickly. The parser expands it to a tree and fills in the default positions for each operator. For example, ⿰ gives (左, 右), ⿸ gives (左上, 中内), and ⿴ gives (中外, 中内). Any `pos` given explicitly in `tree` overrides the default.
- `pos` uses the paper's 11-position vocabulary: 上 下 左 右 中 左上 右上 左下 右下 中内 中外. 中内 and 中外 are enclosure roles, so the renderer draws them as nested boxes rather than grid cells.
- A validator (`zitex check`) flags a `pos` that does not fit its operator, a missing `pos`, and unknown labels. These checks help review and revise the DB data.
- SQLite import and export are postponed (see M5).

## 4. Syntax

**Authoring forms** (all parse to the same tree):

| Form | Example | Notes |
|---|---|---|
| Shape string | `⿱艹⿰氵喿` | Prefix form built on the Unicode IDS operators, so it is interoperable |
| Existing ZiNets net form | `藻(艹+澡)` | Flat; importer converts it to a shape string with the operator guessed or marked `?` |
| Explicit nesting | `藻 = 艹 / (氵 \| (木 / 品))` | Optional later sugar: `/` is ⿱, `\|` is ⿰ |

**LaTeX-side macros** (thin):

```latex
\zi[style=tree]{藻}                % looks up 藻 in the loaded YAML
\zi[style=matrix]{⿰日寺}           % inline expression, no lookup
\ziformula{時}                     % 日 + 寺 → 時
```

## 5. Renderers

- **matrix:** a recursive box layout driven by operators (not a fixed 3×3). Leaves are glyphs. Enclosures nest. Roles are tinted (semantic, phonetic, force-carrier).
- **tree:** TikZ `forest`-style tree. Python emits the full tree, so no LaTeX `child` macro tricks are needed.
- **formula:** `component + component → char`, with pinyin and meaning on request.

Every renderer can emit either a standalone `.tex` snippet (TikZ, no document wrapper, for `\input` into the paper) or a compiled PDF figure. The CLI takes `--emit tex|pdf|both`.

## 6. Fonts and rare components

The 422 elemental characters (元字) include components that no common font has.

1. `fonts.yaml` maps each component to `{font | svg | text-alias}`.
2. The renderer checks glyph coverage with `fontTools` against Noto CJK, then uses the fallback.
3. SVG fallbacks are converted to PDF (Inkscape or `cairosvg`) and included with `\includegraphics`.
4. A coverage report (`zitex fonts --report`) lists components that still have no glyph.

## 7. Milestones

| # | Deliverable | Done when |
|---|---|---|
| M0 | Spec: `docs/DEV/claude/spec.md` with grammar, position table, 20 test characters in `tests/data/chars.yaml` | Reviewed by user |
| M1 | `src/zitex/tree.py`, `loader.py`, `validate.py`: YAML tree loader, shape-string expansion, tree → shape round trip, and the position validator | Done: 16 tests pass on all 23 test characters |
| M2 | `src/zitex/render.py`: tree, formula and matrix output as `.tex` | Done: tree and matrix PDFs for 藻, 時, 愛, 國 plus a formula sheet are in `examples/m2/`; 28 tests pass |
| M2b | `render_math` and `lexicon.py`: equation view with pinyin above and a gloss below each piece, `lang=` option, `collapse` (3 × 口), role-labelled arrow. Same grammar as conceptbook-app (`\underbrace`, `\overset`), so it works in MathJax and XeLaTeX | Done: 36 tests pass; `examples/m2/equations.pdf` checked |
| M3 | `src/zitex/zitex.sty` and the `zitex render` command (one command for batch, single and `--scan` use), `--emit tex\|pdf\|both`, `--scan main.tex` | Done: `examples/demo` builds from a clean checkout with `make`; end-to-end test (scan, build, xelatex) passes; 43 tests pass |
| M4 | `fonts.py`, `fonts.yaml`, `zitex fonts` report, `{name}` components: fallback fonts, SVG images, aliases, boxed label when nothing can draw a glyph | Done: all test-set components covered; fallback, SVG and missing paths tested; 63 tests pass |
| M4b | Zi-Matrix refactor: 11 position codes, per-operator patterns, `<pattern>` and `∷ ⁙` operators, radical rule (`radicals.py`), validator W1-W8, generic flat layout | Done: 92 tests pass; specified in `zi-matrix.md` and `spec.md` |
| M5 | *Postponed.* YAML ↔ SQLite bridge, batch PDF of a character family | Start only after the prototype is accepted and the DB is reviewed |
| M6 | *Postponed.* Hook into the zinets app (`/home/papagame/projects/Proj-ZiNets/zinets_vis`) for export | Same condition as M5 |

Test characters should cover every operator: 時 (⿰), 藻 (⿱ with nesting), 衍 (⿻/⿲ style), 國 (⿴), 同 (⿵), 区 (⿷), 病 (⿸), 句 (⿹), 近 (⿺), 品 (⿳-like), 愛 (4 parts), and a few paper examples (禺, 乍, 巠, 寺, 氢).

## 8. Repository layout (proposed)

```
zinets-latex/
├── docs/{gemini,DEV/claude}/
├── src/zitex/             # Python package: tree.py, loader.py, validate.py, render.py, cli.py
├── src/zitex/zitex.sty   # thin macros (shipped in the package)
├── data/                  # *.yaml character decompositions, fonts.yaml
├── tests/                 # pytest, plus tests/data/chars.yaml
└── examples/demo.tex
```

## 9. Not carried over from the Gemini draft

- `\zimatrix` took 9 arguments and chained into an 11-argument version. This was fragile and hard to read, so it is replaced by an expression plus a recursive renderer.
- `\doublebar` is undefined.
- The 藻 example was decomposed wrongly (澡 placed in a bottom cell). The correct form is 艹 over (氵 + 喿), where 喿 is 品 over 木.
- 中内 and 中外 were drawn as cells in a 3×3 grid. They are enclosure relations.
- `zidecompose` as a TikZ `child` environment is replaced by Python-generated trees.
- SimSun is replaced by Noto CJK.

## 10. Context in the zinets app

- The zinets app stores free-text composition (`character_cache.composition`) in `vis/backend/zinets_cache.sqlite`. The structured 5000-character decomposition DB is separate. It stores positions per component, is not final, and is under review, so this prototype does not touch it.
- The app's markdown network format (`想(相+心)`) is flat and has no layout operators. The importer in the syntax table is the bridge from it.

## 11. Open questions

1. For the 20 test characters, should I draft the YAML with positions myself for you to correct, or will you supply a sample export from the DB?
2. Do you want the validator to be strict (error) or lenient (warning) when `pos` disagrees with the operator? I planned warnings, since the DB is still under revision.

Resolved: positions are stored per component; output is PDF and `.tex`; the SQLite bridge and app hook (M5, M6) are postponed; the engine is XeLaTeX; storage is YAML.

## 12. Relation to conceptbook-app

conceptbook-app (`/home/papagame/projects/digital-duck/conceptbook-app`) already shows character decompositions as MathJax equations (`\underbrace{木}_{arbre} + ... = 森`), but the equation text is written by an LLM. `render_math` generates the same grammar from the validated tree, so structure, positions and repeats come from data and the LLM only needs to supply glosses. Details of the current design: `docs/DEV/zinets/chinese-characters-stem-approach.md` in that repo.
