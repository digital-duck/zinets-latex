# ZiNets-LaTeX: Development Plan

**Open items for the author: section 14. Status of the last stretch: section 13.**

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

1. **Batch:** `zitex render -i data.yaml [--scan doc.tex]` writes snippets (plain TikZ `.tex`) and figures (`.pdf`) for the characters in a YAML file, or for the `\zi{...}` calls in a paper.
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
| M5 | Two data adapters, YAML and SQLite: `-i/--input` on every command, `zitex db-build`, `extract`, `patterns`; zitex's own `zx_*` tables in a separate file, the working DB read only | **Done**: 5,982 characters convert, 223 rows left out and reported; see `db-integration.md` |
| M5b | A self-contained working folder: `zitex setup` (zitex.sty, fonts.yaml detected from this computer), `zitex extract` (chars.yaml, lexicon.yaml, main.tex, snippets), then `xelatex main.tex` | **Done**, and validated by the author |
| M5c | Revisions: `zx_revision`, `zxdb.revise` / `revert`, an elemental flag; they survive `db-build`. First one: 弗 as a primitive elemental character. `*-elemental-decomposed.csv` is the worklist | **Done**: 321 tests; the first revision is in `db/zitex.sqlite3` |
| M6 | Hook into the zinets app (`/home/papagame/projects/Proj-ZiNets/zinets_vis`) | Not started. M5 is done, so the condition is met. First compare the zitex entry format with `graph.yaml` (section 14) |
| M7 | Streamlit app (`src/ui/streamlit/`): review and revise decompositions, generate `main.pdf` for a list of characters | **Built, to be validated next**: checklist in `docs/GUIDE/Streamlit-app.md`. Headless tests pass; not yet looked at in a browser |

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

The questions asked while the prototype was built are all answered: positions are stored per component and written as codes, output is PDF and `.tex`, the engine is XeLaTeX, storage is YAML, the SQLite bridge exists, and warnings are warnings. What is still open is in section 14.

## 12. Relation to conceptbook-app

conceptbook-app (`/home/papagame/projects/digital-duck/conceptbook-app`) already shows character decompositions as MathJax equations (`\underbrace{木}_{arbre} + ... = 森`), but the equation text is written by an LLM. `render_math` generates the same grammar from the validated tree, so structure, positions and repeats come from data and the LLM only needs to supply glosses. Details of the current design: `docs/DEV/zinets/chinese-characters-stem-approach.md` in that repo.

## 13. Status of the last stretch (2026-10-02)

**Done**

- **One input option.** Every command that reads data takes `-i` / `--input` and no positional file argument. `check` takes a comma-separated list. Defaults: `./chars.yaml` for `render`, `check`, `shape`, `fonts`, `patterns`; `db/zitex.sqlite3` (found in this folder or a parent, or `$ZITEX_DB`) for `extract`; none for `db-build`.
- **One render command.** `build` was merged into `render` (`--char`, `--scan`, `-o` file, stem, directory or `-`).
- **Working folder.** `zitex setup -o work/` then `zitex extract -c 器,藻,佛 -o work/` then `cd work && xelatex main.tex`. `zitex.sty` is copied into the folder, so nothing is installed elsewhere. At most 60 characters are extracted, with a warning above that.
- **Database.** `zitex db-build` reads the working database read only, writes the `zx_*` tables to a separate file, and checks the source is byte for byte unchanged. Rows that cannot be converted safely are left out and listed, not guessed.
- **Revisions.** Corrections made by hand live in `zx_revision` of the zitex file and survive `db-build`. The first one makes 弗 a primitive elemental character, so 佛 is 亻 + 弗 (it was 亻 + 弗 expanded into 乀 + 韋, a row that dropped the 丿 stroke of the Shuowen analysis).
- **Streamlit app.** Two pages, review and generate. The logic is in `zitex.review` and `zitex.pipeline`, and `tests/test_ui.py` runs the pages headless.
- **Attribution.** The CC-CEDICT-derived data is attributed in `db/NOTICE.md`, the README, `zx_meta` and the header of every extracted YAML file.
- **Docs.** The tutorial was checked command by command against the current CLI.
- **Tests.** 321 pass, 1 skips (the smoke test on the original database, which is not in the repository; set `ZITEX_REAL_DB` to run it).

**Numbers from the database (read on 2026-10-02)**

| What | Count |
|---|---|
| characters that convert | 5,982 |
| rows left out | 223 (211 hold two or more parts in one position, 6 have one part, 5 have a `?`, 1 inactive) |
| elemental characters that still have a decomposition | 160 |
| components that are neither elemental nor decomposed | 469 |
| characters whose pattern uses `Mi` | 113 (`M-Mi` 102) |
| warnings | 102: W8 (a radical labelled `M`) 88, W7 (overlapping regions) 14 |
| converted characters without pinyin / without an English gloss | 351 / 555 |
| revisions made by hand | 1 (弗) |

## 14. TODO: items for the author to fix or decide

Tick them off here. The worklists are in `db/` (`zitex-quarantine*.csv`) and in the Streamlit app, page 1, section "What to review".

**A. Validate next**

- [ ] **Streamlit app.** Follow the checklist in `docs/GUIDE/Streamlit-app.md`, on a *copy* of the database, and look at the layout in a browser. Only headless tests have been run.

**B. The database, iteration 2 (decisions only you can make)**

- [ ] **160 elemental characters still have a decomposition** (`db/zitex-quarantine-elemental-decomposed.csv`, for example 三 = 一/一/一, 丈 = 一/乂). Most of the ~420 elemental characters should be primitives. Make them so one by one in the app (tick *elemental* and delete the rows), or in a batch in the master database.
- [ ] **Apply the 弗 revision to the master database.** Revisions are kept only in the zitex file. zitex never writes to the working database, so its 弗 row still says 乀 + 韋, and 弗 is not in `t_ele_zi`. The revisions CSV from the app lists what to change.
- [ ] **223 rows left out** (`db/zitex-quarantine.csv`). The 211 with two or more parts in one position (`L = 冖 一`) need a choice for each: split into a nested level, or correct the cell. The 6 one-part rows, the 5 `?` and the inactive 別 need data.
- [ ] **469 components with no decomposition** that are not elemental (`db/zitex-quarantine-undecomposed.csv`, most used first: 卑, 夋, 兆, 亥, 肖). Add a row for each, or add it to the elemental set.
- [ ] **113 `Mi` patterns** (102 `M-Mi`). Re-label them (probably `Mo-D`, `Mo-U` or `Mo-R`) as you planned.
- [ ] **88 radicals labelled `M`** (W8). Each is a data error, or a real exception to the radical rule.
- [ ] **14 overlapping regions** (W7), mostly `U-L-R`, which should be `U-LD-RD`.
- [ ] **Lexicon gaps and quality.** 351 characters have no pinyin and 555 no English gloss. The first dictionary sense is the gloss, and some are too literal (澡 is "bath").
- [ ] **Roles** (semantic, phonetic) are not read from the database. Decide whether `t_ele_zi.phono` or the Shuowen tables should supply them, or whether `readings` in YAML is the place.

**C. Notation decisions still open** (`zi-matrix.md`, section 8)

- [ ] The general `<pattern>` form, the `⁙` symbol, the reading order of labels and the region rule are working proposals. You said you would adjust them later.
- [ ] `LU-LD-R` and `L-RU-RD` have no symbol (they use `<pattern>`).
- [ ] The radical rule's dry run on the test set: 想, 喿 and 禺 as `M-D`; 寺, 巠 and 同 as peers. 虹 is `L-R` in the database, which agrees with the rule.

**D. Licence and publishing**

- [ ] **Confirm the CC-CEDICT version** from the header of the source dictionary file. 4.0 was written from memory, and the attribution rests on the structure of the source tables (`w_cedict_*`, `CL:` and `[pinyin]` notes), not on an entry-by-entry check.
- [ ] **Commit and push.** Many changes since the last commit: the CLI merge, readings, `install-sty`, `setup` and `extract`, the Zi-Matrix refactor, the database adapter, revisions, the Streamlit app and the docs.
- [ ] **Decide whether the demo's build files stay tracked** (`examples/demo/main.pdf`, `main.aux`, `zitex-out/`). They are generated, and `make clean` deletes them.

**E. Integration**

- [ ] **Compare the zitex entry format with `graph.yaml`** (primitives, concepts, applications) before M6, the hook into the zinets app.
- [ ] **conceptbook-app** will depend on zitex. Its LLM-written equations could be replaced by `render_snippet(..., style="math")`. The public function is `zitex.render_snippet`, and the API is not frozen.

**F. For the paper**

- [ ] Use `zitex patterns` for the Figure 5 statistics, so the figure stays in step with the data.
- [ ] Word the "before language" claim as being about the pictographic origin of signs, not about the oracle bone corpus, which is generally regarded as a mature writing system.
- [ ] The sound analysis (dialects, Old Chinese reconstructions as stored hypotheses, a baseline for each statistic) is planned, not started.

## 15. Not verified

- The Streamlit app **in a browser**. The pages run headless and the server starts (health check and home page return OK), but nobody has looked at the layout.
- The `math` output in **MathJax or KaTeX**. It uses only commands both support, but it was only compiled with XeLaTeX.
- **Windows**: snippet file names are now ASCII code points (`u85fb-tree.tex`), which removes the UTF-8 file name risk, but nothing has been run on Windows. Linux works.
- **LuaLaTeX**: only XeLaTeX is supported.
- The `qi-top` example in tutorial section 6 is a placeholder.
- One full test run showed 5 failures that could not be explained or reproduced (several later runs were green).

## 16. TODO: Resolve decomposition DQ issue

The design is settled, and what is left is data quality. This section is the working loop for fixing it. The four worklists below were exported on 2026-10-02 from `db/zitex.sqlite3`, and they match the numbers at the top of the review page.

| Worklist (`db/`) | Rows | What is wrong | How to fix it in the review app |
|---|---|---|---|
| `review-elemental-decomposed.csv` | 160 | elemental characters that still have a decomposition (三 = 一/一/一, 丈 = 一/乂) | open the character, delete all rows of the **Revise** table, tick *elemental*, **Save revision** (most should become primitives) |
| `review-left-out.csv` | 222 | rows that could not be converted (211 with two or more parts in one position, such as `L = 冖 一`; 6 with one part; 5 with `?`; 1 inactive) | open the character (it says "not in this database"), enter its parts and positions, **Check the change**, **Save revision** |
| `review-with-warnings.csv` | 102 | W8 (a radical labelled `M`, 88) and W7 (overlapping regions, 14, mostly `U-L-R` that should be `U-LD-RD`). The `codes` column separates them | change the positions in the **Revise** table so the warning clears, or leave it and write the reason in **Why** when it is a real exception to the radical rule |
| `review-revised.csv` | 2 | revisions made so far (弗, 他). Not an error list: it is the record of what you already changed | check that each one is still what you want |

Each file has a `char` column. Sort and filter in a spreadsheet to plan the work, and use the app to make each change.

### The planned route: fix in the original app, then rebuild here

The author's original Streamlit app, the one used to decompose the 6,000 characters, edits the master database (`zi.sqlite3`). It is fast and knows the data, so the main route is:

1. Use `db/review-*.csv` as the worklist, and fix the characters in the original app.
2. Take the finished `zi.sqlite3` and put it somewhere outside the repository (zitex only reads it, and the master is not committed).
3. Rebuild the derived database here:
   ```bash
   zitex db-build -i path/to/zi.sqlite3 -o db/zitex.sqlite3 --report db/zitex-quarantine.csv
   ```
4. Check, export the worklists again, and commit `db/`:
   ```bash
   zitex check -i db/zitex.sqlite3
   zitex review-export -i db/zitex.sqlite3 -o db
   ```
   The metrics and the CSV files should have shrunk by what you fixed. Whatever is still listed is what remains.

**Before step 3, deal with the two existing revisions** (弗 and 他, in `db/review-revised.csv`). They live only in the zitex file, and `db-build` applies them again on top of the new master. If the master already has the same fix (弗 as a primitive in `t_ele_zi` with no parts, 他 = 亻 + 也), nothing changes. If you change either character differently in the master, the old revision would override you. So either make the master agree, or revert the revision in the review app first. After the rebuild, `review-revised.csv` should list only revisions you still want.

The review app in this repository is then for **checking the result**, and for the odd one-off fix: after the rebuild, look at the lists and open any character that still looks wrong.

### The loop (fixing in this repository's review app instead)

1. **Fix** a batch in the review app (`streamlit run src/ui/streamlit/app.py`). Each **Save revision** is stored in `zx_revision` of the zitex file, with the original row so **Revert to the original** works. Work on `db/zitex.sqlite3` itself, or on a copy that you later copy back.
2. **Check progress** in the metrics row at the top of the page. The goal is `left out` 0, `elemental, decomposed` 0 (or the number you decide to keep), and `with warnings` down to the real exceptions.
3. **Export again** when you want a fresh worklist:
   ```bash
   zitex review-export -i db/zitex.sqlite3 -o db
   ```
   It only reads the database, and it overwrites the four `db/review-*.csv` files.
4. **Rebuild** when the batch is done and you want the master data to carry the fixes:
   ```bash
   zitex db-build -i path/to/zi.sqlite3 -o db/zitex.sqlite3 --report db/zitex-quarantine.csv
   ```
   It builds the tables afresh from the master database, and **applies your revisions again on top** (it prints `re-applied N revision(s)`). The master database is opened read only and is never changed.
5. **Check after the rebuild.** Open the review page again: the metrics should show your fixes, and `zitex check -i db/zitex.sqlite3` should agree. Then commit `db/` (the database and the CSV files).

### Decide where the truth lives

There are two places to fix a character, and you should choose one for each batch.

- **In the app, as a revision** (steps 1 to 4 above). The fix lives in the zitex file. It survives every `db-build`, but the master database still has the old row.
- **In the master database** (`t_zi_part`, `t_ele_zi`), then `db-build`. The fix is part of the source. Once you have done this for a character, **revert or delete its revision in the app**: a revision is applied on top of the rebuilt row, so a stale one would override the master.

The revisions list (`review-revised.csv`, or **Download the revisions (CSV)** on the page) is what to copy into the master database when you want the two to agree. After that the revisions can be reverted, and the master alone is the truth again.

### Suggested order

Start with the groups that remove the most noise for the least thought:

- [ ] **Elemental, decomposed (160).** Mostly mechanical: make each a primitive. This also removes false structure from every character that uses it.
- [ ] **W7 (14).** Mostly one pattern, `U-L-R` to `U-LD-RD`.
- [ ] **W8 (88).** One decision per character: a data error, or an exception to the radical rule. Write the reason in **Why** for the exceptions, so it is kept with the revision.
- [ ] **Left out (222).** The 211 multi-part cells need a choice each (a nested level, or a corrected cell). Do the 6 one-part rows, the 5 `?` and the inactive row by hand.
- [ ] **Then** the 469 undecomposed components and the 113 `Mi` patterns (section 14, B), which are not in these four lists.
- [ ] **Rebuild and commit** `db/zitex.sqlite3` and the CSV files after each batch.
