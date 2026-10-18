# Review of zitex (paper and repository): Claude

Reviewer: Claude (Anthropic), 11 October 2026. Repository at commit `879a19b` ("refine").

**What I ran.** Python 3.13, XeTeX from TeX Live 2023 (Ubuntu), Noto Serif CJK and Noto Color Emoji installed.
- The test suite.
- `examples/pict/build.sh` and `docs/paper/arxiv/make-arxiv.sh`.
- A clean compile of the arXiv tarball with the system CJK fonts hidden.
- The paper's own commands (`zitex setup` and `zitex extract -c 器,藻,佛`).
- Small scripts for the failure cases reported in Q7.
- KaTeX 0.16 and MathJax 3 on the equation snippets.

Line numbers refer to that commit. "Verified" means I ran it. Everything else is from reading.

---

## 1. Verdict

zitex contributes a small, working and reproducible pipeline: Python turns a character record into ASCII-named LaTeX snippets, and a 90-line package inputs them. I rebuilt every snippet in the paper byte for byte from the data in the repository, and 347 tests pass.

The paper is **not ready for arXiv yet**, though it is close: the new picture view is presented with statements about oracle bone script and character origins that a paleographer would reject and that contradict the paper's own disclaimer. The motivation rests on claims about "manual work today" with no related work behind them, and the font subset in the arXiv source ships without its licence.

**Single most important fix:** rewrite the oracle bone and "sun + moon" framing so that it claims only what the figures show. Mark 工 in 虹 as the sound component with zitex's own `arrow=role`, give each glyph's source, and drop "modern characters have kept the sound and the meaning". Then add one paragraph of related work.

---

## 2. Findings

### Q1. Claims against evidence

Each claim from the abstract (A) and introduction (I) is marked **demonstrated**, **asserted**, or **contradicted**.

| # | Claim (main.tex line) | Status |
|---|---|---|
| A1 | Characters "began as pictographs, as the oracle bone script shows" (29, again 42, 187) | Asserted. Contested in this form (see Q2). |
| A2 | Every character has sound, shape, meaning (29, 47) | Asserted. This is the traditional 形音義 framework and should be cited as such. |
| A3 | Presenting them together "consistently is manual work today … none of it is tied to the data" (30–31, 48–51) | Asserted, no evidence, partly **contradicted**. `xpinyin` adds pinyin automatically, and Make Me a Hanzi and the CUHK database tie decompositions and ancient forms to data (Q3). |
| A4 | "makes the figure a function of the data" (32) | **Partly demonstrated.** I regenerated all 17 snippets in `docs/paper/arxiv/zitex-out/` byte-identical. But the output also depends on the machine (see note below). |
| A5 | A character is a short entry with decomposition and positions (32–33) | Demonstrated (`chars.yaml`). |
| A6 | Python validates the data (33) | Demonstrated (`zitex check`). It only emits warnings, which the paper says. |
| A7 | One self-contained snippet per character and view (33–34) | Demonstrated. "Self-contained" means the document still loads `zitex.sty`, amsmath, graphicx and TikZ. |
| A8 | Picture row so "each part shows its sound, its shape and its meaning" (35–36) | **Contradicted as worded.** The shape is the character row. An emoji pictures the meaning (☀️, 🌈) and an oracle bone glyph is an ancient form, so the row is not "shape". |
| A9 | "A short LaTeX package only includes those snippets" (36) | Mostly demonstrated. The package also sets the CJK font and a char class (`zitex.sty:23–27`), so "only" overstates. |
| I1 | OBS "still shows the pictures: the sun is a circle…" (42–43) | Asserted. See Q2. |
| I2 | "Modern characters have kept the sound and the meaning" (44) | **Contradicted** by historical phonology and semantics (Q2). |
| I3 | Teachers and researchers keep placing the ancient glyph next to the modern one (44–45) | Asserted, no citation. |
| I4 | Manual figures are "slow … differ … must be redone" (50) | Asserted. No example, timing or comparison. |
| I5 | The reaction view "is used to teach characters … and to analyse its structure computationally" (54–55) | Asserted. Supported only by the author's own paper [1]. |
| I6 (i) | Revising the record revises the figure (57–58) | Demonstrated. Snippets regenerate deterministically. |
| I6 (ii) | The notation records where each part sits, "which a flat sequence of components does not" (58–59) | **Partly contradicted.** IDS are not flat: ⿰ ⿱ ⿴ encode arrangement, and cjk-decomp has typed relations including repetition. Also `L-M` and `L-R` draw identically (Figure 2, 佛), so the extra information is not visible. |
| I6 (iii) | Sound, shape, meaning "laid out the same way for every character" (59–60) | Shown for 5 characters only. A character with no decomposition renders as `日 = 日` (Q7). Emoji pictures change with the installed emoji font. |
| I6 (iv) | The LaTeX side is small and the logic is tested (60–61) | Demonstrated: 90-line `.sty`, 347 passing tests. |
| I6 (v) | "the source database is never modified" (61) | **Contradicted.** `zitex db-build --in-place` writes the zx_ tables into the source database after a backup (`cli.py:312–313, 331`). Its own help text says "never changed" (`cli.py:309`). |
| I7 | Section 4 shows the oracle bone glyphs of the six characters (61–62) | Shown. But the 月 image comes from HWOBC, a modern handwritten collection (`obs/picts.csv`, source `H_0815_…`), not from an inscription. |

Note on A4: besides the data, the output depends on:
- environment variables or a `.env` file read from the current folder (`config.py:16–36`);
- the installed emoji font (my emoji PNGs differ from the committed ones);
- the fallback fonts `zitex setup` detects on the machine (`fonts.yaml`);
- glyphs and emoji that were chosen by hand.

**Fixes**
- A4: say "a function of the data and a small configuration". Record the emoji font version in `build_manifest.json`.
- A8: call the row "picture", not "shape".
- I2: remove the sentence.
- I6 (ii): change to "IDS give the arrangement; zitex adds a named position for every part, including levels with three or more parts".
- I6 (v): either delete `--in-place` or say "is opened read only by every command except the opt-in `db-build --in-place`".
- A3 and I4: either cite evidence or soften to "is usually assembled by hand", and add Q3's related work.

### Q2. Oracle bone script statements

The paper says it makes no claim about etymology (line 217), but it makes several.

- **Blocker: line 176 reads 虹 compositionally.** "Reading 日 + 月 = 明 as sun and moon making bright, and 虫 + 工 = 虹 in the same way." The emoji figure (🐛 + 🛠️ = 🌈, "insect + work = rainbow") states the same thing visually.
  - The standard analysis since the *Shuowen* is phono-semantic (形聲): 虫 is the semantic part and 工 gives the sound (gōng/hóng). Shuowen says 从虫工聲. I am confident of this but have not checked it against a printed edition.
  - "In the same way" therefore asserts an etymology, and a wrong one.
  - **Fix:** render 虹 with `arrow=role` so the arrow reads "sound: gōng". zitex already supports this (`render.py:156–163`). Give 工 the meaning "(sound)" or no gloss, and say in one sentence that 明 and 虹 were chosen because they are built differently.
- **Important: the oracle bone glyph above modern 虫 + 工 implies a derivation that did not happen.** The chosen 虹 glyph (line 202, "an arch with a head at each end") is a single drawing of a two-headed creature. It is not composed of oracle bone 虫 and 工; the 虫 + 工 form is later. Putting oracle bone 虫 and 工 over the modern parts invites the reader to add them up.
  - **Fix:** add a sentence saying the ancient form of the whole character need not contain the ancient forms of its modern parts, and that 虹 is an example.
- **Important: 虫 in oracle bone script.** It depicts a snake (read huǐ, 虺), and the chosen glyph looks like one, while the emoji is a caterpillar and the gloss is "insect". This is exactly the "creature drawn as what it is" claim (line 43) failing on the paper's own example.
  - **Fix:** gloss the result character only, or add the note.
- **Important: "Modern characters have kept the sound and the meaning" (line 44).**
  - Pinyin is modern Mandarin. Shang-period pronunciation is reconstructed very differently; see Baxter and Sagart, *Old Chinese: A New Reconstruction*, OUP 2014.
  - Meanings have drifted too; 虫 is an example.
  - **Fix:** delete the sentence, or limit it to "the modern character is the descendant of the ancient form".
- **Important: "Chinese characters originated as pictographs" (lines 29, 42, 187).** Specialists would qualify this.
  - Pictographs are a minority of oracle bone graphs.
  - Phonetic loans and phono-semantic compounds are already common in the oracle bone corpus.
  - Some early signs, such as numerals and 上/下, are not pictures.
  - See Qiu Xigui, *Chinese Writing*, trans. Mattos and Norman, Society for the Study of Early China, 2000; Boltz, *The Origin and Early Development of the Chinese Writing System*, American Oriental Society, 1994.
  - **Fix:** "Many early characters were pictographs, and oracle bone script often still shows the picture."
- **Minor:**
  - "The sun is a circle" (line 43): carved 日 is often angular or square because it was cut with a knife. Write "a circle or a square with a mark inside".
  - "turtle shells and animal bones": mostly turtle plastrons and ox scapulae.
- **Minor: glyph provenance and period are not given.** `obs/picts.csv` records the source of every glyph, which is good practice.
  - 日 is from 合36169 (黃組, late period); 明 from 合11498 and 工 from 合9472 (both 賓組, Wu Ding period).
  - 月 is from HWOBC, which is handwritten. 虫 (`G_1372_甲骨文0`) has no rubbing number.
  - One equation thus mixes periods, and includes one modern handwritten form, without saying so.
  - **Fix:** add a footnote or caption line listing each glyph's 合集 number, period group or "HWOBC (handwritten)". Prefer a glyph traced from an inscription for 月.
- **Minor: 明 (line 201).** "A crescent next to a small box and not a sun and a moon" describes this one glyph, which is fine. But "and not a sun and a moon" reads as a verdict, and other oracle bone forms of 明 do show 日 + 月.
  - **Fix:** "In the glyph chosen here, 明 is a crescent next to a small box (other oracle bone forms show 日 and 月)."
- **Minor: data outside the paper.** `data/ele_chars` assigns an oracle bone glyph to 亻 (`picts.csv`). The 亻 form is a later component variant; oracle bone script writes 人. Glyphs for component variants that did not exist then should be marked as such.

Does the text keep to "no claim about etymology"? **No**: lines 44, 176 and 201–202, plus the emoji figure. Line 217 should either be kept and backed by these fixes, or replaced by "We present one standard analysis per character and cite it."

### Q3. Related work

Line 210 says no survey was done. That is honest, but a reader will ask at once how this differs from the following. One sentence each is enough. I checked each URL unless I say otherwise.

- **Pinyin and ruby in LaTeX**
  - `xpinyin` (https://ctan.org/pkg/xpinyin) adds pinyin to characters automatically. Say why it is not used, or how the per-part pinyin of an equation differs.
  - `pxrubrica` (https://ctan.org/pkg/pxrubrica) does ruby for pTeX/upLaTeX. `luatexja-ruby` is part of LuaTeX-ja; I did not fetch it.
- **IDS resources and the operators**
  - Unicode 15.1 (2023) added ⿼ ⿽ ⿾ ⿿ (https://en.wikipedia.org/wiki/Ideographic_Description_Characters; Unicode announcement https://blog.unicode.org/2023/09/announcing-unicode-standard-version-151.html). The paper should list them, say whether zitex reads them, and explain why ∴ ∵ ∷ ⁙ are needed beyond ⿲ ⿳ and the new characters.
  - BabelStone IDS by Andrew West (https://www.babelstone.co.uk/CJK/IDS.HTML) covers all unified ideographs as of Unicode 16.
  - cjk-decomp (https://github.com/amake/cjk-decomp) records about 75,000 typed decompositions. Its `r.*` types cover repetition, which bears directly on the claim that standard data cannot keep three repeated parts at one level. Say that it is unmaintained and that zitex differs by giving a position per part.
  - cjkvi-ids is already cited.
- **Decomposition, roles and stroke order**
  - Make Me a Hanzi (https://github.com/skishore/makemeahanzi) has IDS for 9,000+ characters and an etymology field (pictographic / ideographic / pictophonetic, with semantic and phonetic components). That is the same idea as zitex's readings and roles, and should be cited and compared.
  - Hanzi Writer (https://hanziwriter.org) animates stroke order from that data. Mention it as out of scope.
- **Glyph evolution and ancient forms**
  - The CUHK Multi-function Chinese Character Database (https://humanum.arts.cuhk.edu.hk/Lexis/lexi-mf/) has archaic forms, "componential trees" (部件樹) and etymologies. It is the closest existing presentation of a tree view with ancient forms; zitex differs in producing LaTeX from data you control.
  - Richard Sears, Chinese Etymology (https://hanziyuan.net) lists oracle bone, bronze and seal forms per character.
  - 小學堂 字形演變 (https://xiaoxue.iis.sinica.edu.tw/yanbian) shows glyph evolution. I only saw the URL and a PDF guide, so verify the maintainer before citing.
- **Oracle bone datasets**
  - HUST-OBC is cited. Its README lists its own sources (新甲骨文編, 甲骨文六位數字碼, GuoXueDaShi, YinQiWenYuan, HWOBC); say that the glyphs used come from those.
  - EVOBC (arXiv:2401.12467) is an evolution dataset across script stages, relevant if a later version shows several stages.
  - OBC306 exists as a recognition benchmark, but I did not fetch it, so I am unsure of the citation.
- **The reaction metaphor in typesetting**
  - `mhchem` and `chemfig` are the obvious precedents for "chemistry-style" equations (CTAN; not fetched). One clause would do.

### Q4. Design

- **One `array` grid instead of stacked `\underbrace` labels: good decision.** Page 5 of `main.pdf` shows the picture and meaning rows aligned across parts, which stacked braces cannot guarantee (`docs/DEV/claude/readme-zimath.md:31–35`).
  - **Important: it has no web equivalent.** KaTeX rejects the column spec (`@{\hspace{3pt}}`, verified). MathJax accepts the array but would print `\parbox[t]{…}` inside `\text{}` literally, so even a picture-free grid is unusable on the web. Web users therefore get a different layout (the `math` view) for the same record.
  - **Fix:** add an HTML/CSS-grid renderer for the same cells, or emit a MathJax-safe variant (plain `\text{sun}`, `{c c c}` columns) when there are no pictures.
- **A separate opt-in style (`pictmath`): good decision.** The existing math output is unchanged, and `test_pictmath_is_not_in_the_default_styles` checks it.
  - **Important: the cost is a name space (style × set × language × reading) that two independent parsers must agree on.** The regex scanner in Python and xkeyval in the package already disagree (Q7, findings 1 and 2).
  - **Fix:** let the package write the names it needs, BibTeX-style (`\immediate\write` of each requested snippet name to `\jobname.zitex`), and have `zitex render --jobs main.zitex` read that file. Then there is one source of truth, and macros that wrap `\zimath` work too.
- **Named picture sets chosen per call, with no fallback to emoji: good.** It keeps an oracle bone figure from silently mixing in an emoji (line 203–204).
- **Emoji rasterised to PNG at build time: necessary for XeLaTeX, but it undermines "consistent".**
  - The pictures depend on which emoji font is installed: Apple Color Emoji on macOS (`lexicon.py:16`) and Noto elsewhere draw differently. Even two Noto versions differ: my 6 emoji PNGs differ from the committed ones.
  - **Fix:** vendor the PNGs from a pinned noto-emoji release, or record font name and version in the manifest.
  - Choosing an emoji is itself an interpretation (🛠️ for 工 in 虹); see Q2.
- **What breaks, and for whom:**
  - **Overleaf.** The Python step cannot run there. Users must upload `zitex-out/` with `picts/` and `zitex.sty`. ASCII file names make that workable; the paper should say so. Font availability on Overleaf not verified.
  - **LuaLaTeX and pdfLaTeX.** `zitex.sty` requires xeCJK, which is XeTeX only. A LuaLaTeX path through `luatexja` or `ctex` would be the next step; otherwise state "XeLaTeX only" in the abstract.
  - **Long equations.** Known limit.
  - **Right-to-left glosses.** Hebrew or Arabic glosses in `\parbox` without `bidi` are untested and will likely render in the wrong order.
  - **Accessibility.** Pictures have no alternative text, and the PDF is untagged (xpinyin's CTAN page notes it is tagged-PDF incompatible too). Low priority, but worth a line in the limitations.
- **Minor: settings are baked into each snippet.** The picture size (`render.py:241–250`) is read from the environment or a `.env` file in the current folder when the snippet is built, then written with `\providecommand`. In a document mixing snippets built with different settings, the first one wins. Document this, or make the size a package option only.

### Q5. Reproducibility

**Yes, section 4 can be rebuilt from the repository alone (verified).**
- `zitex setup -o work && zitex extract -c 器,藻,佛 -o work` against `db/zitex.sqlite3` produced the same `chars.yaml` entries and byte-identical snippets for 器, 藻 and 佛.
- `zitex render --scan main.tex` in `docs/paper/arxiv` reproduced the five picture snippets byte for byte.
- `examples/pict/build.sh` and `make-arxiv.sh` both succeed.
- The tarball's `main.tex` and `zitex.sty` are identical to the repository's.
- The test suite gave 347 passed and 3 skipped (Streamlit, Inkscape, real database). **The six failures in `test_pipeline.py` and `test_ui.py` that the author sees did not occur here**; the UI tests were skipped because Streamlit is not installed. That points to something environment-specific on the author's machine.

**Hidden or under-documented dependencies**, ranked:
1. **Important: xeCJK.** It is not in a basic TeX Live install. On Debian or Ubuntu it is in `texlive-lang-chinese`, and `build.sh` failed with "File `xeCJK.sty' not found" until I installed it. **Fix:** name the package per distribution in the README, and check for it in `build.sh` the way it checks for `xelatex`.
2. **Important: Pillow.** It is required for emoji pictures but missing from `pyproject.toml` dependencies (only pyyaml, click and fonttools are listed). **Fix:** add an extra, `pict = ["Pillow"]`.
3. **Important: Noto Color Emoji and `fc-match`.** Without them, emoji pictures are silently omitted (`lexicon.py:103`, see Q7). Windows has no default path.
4. **Minor: Noto Serif CJK SC.** Without it the package falls back to FandolSong, so figures look different with no message beyond a font switch.
5. **Minor:** `zitex setup` writes a machine-specific fallback list (here WenQuanYi Zen Hei, AR PL UMing, Unifont).
6. **Minor:** `pdfinfo` (poppler-utils) is used by `make-arxiv.sh`; Inkscape only for SVG glyphs.
7. **Minor:** Python ≥3.10 is declared; I tested 3.13 only.
8. **Not reproducible from the repository:** how the oracle bone glyphs were *chosen*. The export script is in Orascope (`obs/lexicon.yaml` header), not here. The PNGs and `picts.csv` are present, so the result is auditable but the selection cannot be rerun.
9. **Minor:** `db/zitex.sqlite3` records `quarantined: 223` in `zx_meta`, but `zx_quarantine` has 222 rows. The paper quotes 223 (line 216).

### Q6. Licensing and data

- **Important: the OFL font subset ships without its licence.**
  - Neither `docs/paper/arxiv/fonts/` nor the arXiv tarball contains the OFL text. `fonts/README.txt` only links to it.
  - The subset also dropped name IDs 13 and 14, the licence description and URL, which the original font carries (verified with fontTools).
  - The OFL requires the copyright notice and licence to accompany every copy of the font software, including modified versions such as subsets.
  - **Fix:** copy `LICENSE` from noto-cjk into `fonts/OFL.txt`, add it to the tar line in `make-arxiv.sh`, and regenerate the subsets with `--name-IDs='*'`. The subset's names do not use the reserved name "Source", so keeping "Noto Serif CJK SC" is fine. Bundling the subset in an arXiv source is then allowed.
- **Important: choose the arXiv licence with the NC images in mind.** HUST-OBC is CC BY-NC 4.0 (confirmed in the dataset paper, arXiv:2401.15365, data records).
  - If the paper is released on arXiv as CC BY 4.0 or CC BY-SA 4.0, it would purport to allow commercial reuse of those figures.
  - **Fix:** choose arXiv's non-exclusive distribution licence, or CC BY-NC-SA 4.0. Put "Glyphs: HUST-OBC, CC BY-NC 4.0" in the figure's own text, not only in the acknowledgements.
  - I did not re-check arXiv's current licence menu.
- **Minor: MIT code and CC BY-NC images in one repository.** This is acceptable when clearly marked, and `NOTICE` does mark it well. It names the folders, source, licence, changes and that it is not legal advice; that is better than most repositories.
  - Risk: GitHub shows "MIT" for the whole repository. **Fix:** add a short `LICENSE` file (CC BY-NC 4.0 plus attribution) inside each image folder (`data/ele_chars/`, `examples/pict/obs/`, `docs/paper/arxiv/obs/`), or move the images to a separate data repository.
  - They are already excluded from the Python package (`pyproject.toml` package-data covers only `zitex.sty` and `templates/*`, verified).
- **Minor: upstream rights.** HUST-OBC's images come partly from a published book (新甲骨文編) and websites. The NC licence is the dataset authors' grant, and NOTICE could say plainly that upstream rights in the hand copies are not cleared by it. The current "check the dataset's own terms" is close.
- **Minor:** `db/NOTICE.md` lists `zitex.sqlite3` and the quarantine CSVs, but `db/` also holds `zitex-orig.sqlite3` and four `review-*.csv` files derived from the same data. Add them.
- **Minor: CC BY-SA glosses.** The paper carries a handful of CEDICT glosses ("aquatic grasses", "device"), attributed in the acknowledgements. That is adequate for so little text.
- **Minor:** `pyproject.toml` has the keyword `"etymology"`, which contradicts line 217, and `Paper = arXiv:2502.19428`, which is the model paper, not this one.

### Q7. Code quality

All findings below were reproduced with small inputs unless marked "from reading".

**Important**

1. **`--scan` picks the wrong default language** (`cli.py:219`).
   - A call without `lang=` is rendered in the first `-l` language, but `zitex.sty` asks for `\zitexlang`, which defaults to `en` (`zitex.sty:30`).
   - With `zitex render --scan a.tex -l zh`, `\zimath[pict]{明}` wrote `u660e-pictmath-zh.tex`, while XeLaTeX looked for `u660e-pictmath-en.tex` and printed a red `[明?]`.
   - **Fix:** default to `"en"` as `extract` already does (`cli.py:549`), or better, follow `\zitexsetlang`.
2. **Spaces in options split the two sides** (`build.py:62–64`).
   - `\zimath[pict = obs, lang = zh]{明}`: the scanner keeps the keys as `"pict "` and `"lang "`, so it writes `u660e-math-en.tex`. xkeyval trims the spaces and asks for `u660e-pictmath-obs-zh.tex` ("Missing" warning, red mark).
   - **Fix:** `kv = {k.strip(): v.strip() …}`, and test option variants through `scan_tex`. The existing end-to-end test builds its jobs by hand (`tests/test_pict.py:196–214`), so it does not cover the scanner.
3. **A picture value that is neither an image nor a drawable emoji stops the LaTeX build, and zitex exits 0** (`lexicon.py:102–104, 126–127`; `build.py:160`).
   - `日: {pict: sun}` passes `get_pict` as an "emoji", so the snippet references `picts/u65e5.png`. `emoji_to_png` then returns False and nothing is written.
   - XeLaTeX stops with "Unable to load picture … u65e5.png".
   - The paper's own listing writes `pict: <emoji: sun>` (main.tex:168–170), which a reader will copy and hit exactly this.
   - It also contradicts line 96–97: "a missing file gives a warning … so a long build is not stopped".
   - **Fix:** decide the kind once, write the file before promising the name, and warn on failure. Show real YAML in the paper (`pict: "☀️"`, as in `examples/pict/lexicon.yaml`).
4. **A missing picture file is silently dropped** (`lexicon.py:85–94`).
   - `日: {pict: nosuch/u65e5.png}` gives an empty cell, exit code 0, and no message.
   - For a figure whose point is the picture row, this should warn and be listed in `build_manifest.json`.
   - The same silence applies when no emoji font is found (`lexicon.py:103`).

**Minor**

5. **A character with no decomposition renders as `日 = 日`** (`render.py:189–190`, `279–280`; also `render_formula`). The left side has no pinyin or gloss while the right side does. Elemental characters are the core of the model, so render them as a single column.
6. **`render_math(..., pinyin=False)` without a lexicon still prints the result's pinyin** (`render.py:204`): the condition falls through to `e.pinyin`.
7. **`merge_file` crashes on an empty entry** (`lexicon.py:154–155`): `日:` with no value gives `AttributeError: 'NoneType' object has no attribute 'get'`. Skip it or report the file and key.
8. **`ZITEX_EMOJI_FONT` is ignored unless its file name contains "emoji"** (`lexicon.py:25`). Windows' `seguiemj.ttf`, for example, would be rejected silently. Apply the name filter only to the `fc-match` result.
9. **The emoji size is fixed at 109 px** (`lexicon.py:37`), the one Noto strike. Apple Color Emoji (`lexicon.py:16`) has other strikes; from reading, FreeType may raise "invalid pixel size", uncaught. Not verified on macOS.
10. **`emoji_font()` runs `fc-match` in a subprocess on every `get_pict` call** (several per character per job). Cache it with `functools.cache`.
11. **The scanner regex `\{(.)\}`** (`build.py:37`):
    - misses `\zimath {明}`;
    - misses calls inside user macros;
    - does not read `\zitexsetpath`, so a document that sets another path gets its snippets written to the wrong folder.
    
    The `.zitex` job-file design in Q4 removes this whole class.
12. **`compile_pdf` discards XeLaTeX's output** (`build.py:88–92`), so "failed to compile" comes with no reason. Keep the last lines of the log.
13. **`db-build --in-place`** contradicts the command's own docstring and the paper (Q1, I6 v).

**Where `zitex.sty` and Python could disagree**

- **Agree (verified):** the file name scheme `u<hex>-<style>[-<set>][-<lang>][@reading]`. `\int_to_hex:n` gives lower-case hex, matching `f"u{ord(ch):x}"`.
- **Disagree:**
  - the default language (finding 1);
  - whitespace in options (finding 2);
  - anything not a literal `\zi…{X}` in the source (finding 11);
  - characters written with a variation selector, where the package's `` `#1 `` takes the first code point and the regex takes one character.

**Missing tests**
- Scanner-to-package agreement for option variants and for `-l` without `en`.
- Leaf characters in `math` and `pictmath`.
- Invalid or missing pictures.
- `emoji_to_png` failure paths.
- A check that the arXiv build log has no "Missing character" (see Q9).

### Q8. Writing

- **Important: the title over-claims.** zitex does not decompose characters; it typesets decompositions given to it. **Suggestion:** "Typesetting Chinese Character Decompositions from Data with zitex".
- **Important: repetition.**
  - "Began as pictographs" appears three times (lines 29, 42, 187).
  - "XeLaTeX only / not in MathJax" appears three times (106–107, 116, 212–213).
  - "A part without a picture has an empty cell" appears twice (112, 203–204).
- **Important: the "Readings" paragraph (118–120) describes a feature that is never shown.** Either show it (it is the honest way to present 虹, see Q2) or cut it.
- **Minor: "Every character therefore has three dimensions" (47).** "Therefore" does not follow from the preceding paragraph on pictographs.
- **Minor: overfull line.** Lines 140–142 run 16 pt into the margin (log of the clean build, visible on page 3).
- **Minor: the radical rule is described inaccurately (88–89).**
  - The paper says the radical goes to `L` and the other part to `M`. The code puts a right-side radical at `R` (部 → 咅 `M`, 阝 `R`, verified).
  - When both parts are Kangxi radicals the rule does not apply: 明, 到 and 虹 all come out `L-R`. Since 日 月 木 口 人 女 子 工 虫 are all Kangxi radicals, that is common.
  - **Fix:** describe the rule as implemented, and say when it does not apply.

**Three sentences to cut first**
1. Abstract, lines 36–37: "We describe the notation, the design, the handling of fonts and of the source database, and the limits of the present version." It is boilerplate.
2. Introduction, lines 54–55: "This view is used to teach characters, to study how the writing system is organised, and to analyse its structure computationally~\cite{gong2025}." It is unsupported beyond a self-citation.
3. Section 4, lines 203–204: "In the same way the set is optional for each character: a part with no glyph in the set has an empty cell and is not replaced by an emoji." It repeats line 112.

**The question a sceptical reader will ask:** *"What does this give me that twenty lines of `\overset`/`\underbrace` macros and a small YAML-to-macro script would not, and has anyone other than the author used it for a real document?"*

The paper shows five characters and no larger document, timing, or user. A single figure would answer it: one page of 30–50 equations generated from the database for a teaching handout, with the command that made it.

### Q9. arXiv readiness

- **It compiles (verified).** I extracted the tarball into an empty folder and compiled it twice with XeLaTeX (TeX Live 2023), with only TeX Live's own fonts visible to fontconfig. It produced 6 pages with no errors and no "Missing character".
  - Every CJK character in `main.tex` and the snippets, including ∴ ∵ ∷ and ⿰ ⿱, is in both subsets (verified with fontTools).
  - arXiv's 00README documentation lists `xelatex` as a supported compiler and TeX Live 2025 and 2023 as available (https://info.arxiv.org/help/00README.html). I did not test TeX Live 2025.
- **Risks that could make it fail or differ from the local PDF:**
  1. **Important: silent glyph loss on the next edit.** If a character is added to `main.tex` without regenerating the subset, XeLaTeX only warns, and the character disappears from arXiv's PDF.
     - The same happens if `fonts/` is dropped: `main.tex:11–12` uses `\IfFileExists` and silently falls back to FandolSong on arXiv.
     - **Fix:** make `make-arxiv.sh` fail when `main.log` contains "Missing character". Make the subset unconditional (error, not fallback). Regenerate the subset from `main.tex` plus `zitex-out/*.tex` inside the script.
  2. **Important: the licence file is missing from the source** (Q6).
  3. **Minor: hand-made `00README.json`.** arXiv says the file is normally generated during submission and need not be created by hand. Keep it, since it is how XeLaTeX is selected, but check after upload that it was accepted as written. I did not verify the `sources` key format.
  4. **Minor: the committed tarball can go stale.** `zitex-arxiv-src.tar.gz` is in git. It currently matches `main.tex`, but uploading it after a later edit would ship old text. Build it in CI, or remove it from the repository.
  5. **Minor: `make-arxiv.sh` packs the committed `zitex-out/` without regenerating it.** Add a `zitex render --scan main.tex …` step so the snippets cannot lag behind the data.
  6. **Minor: different glyphs on regeneration.** The subset was made from Noto Serif CJK 2.001; regenerating it from a newer version changes outlines (佛 and 字 differ from version 2.003 here). Pin the version in `fonts/README.txt`.
- **Subject class.**
  - **Primary: cs.DL** (Digital Libraries), whose scope "covers all aspects of the digital library design and document and text creation" (https://arxiv.org/archive/cs). A typesetting tool for documents fits that.
  - **Cross-list: cs.CL.** Its scope is NLP; the work touches Chinese lexical data but contains no NLP method.
  - **Not cs.HC:** there is no user study or interface evaluation.
  - arXiv moderators may move it, so state the document-production purpose in the first paragraph.

---

## 3. Not verified

- **TeX Live 2025, arXiv's own build service and the `00README.json` `sources` key.** Settle by uploading as a draft and comparing arXiv's PDF with the local one.
- **macOS and Windows.** Apple Color Emoji at 109 px, Windows emoji fonts and paths. Settle by running `examples/pict/build.sh` on both.
- **Overleaf** (fonts available, upload workflow) **and LuaLaTeX.** Settle with a test project.
- **The six failing tests on the author's machine.** They passed here; Streamlit UI tests were skipped. Settle by sharing the failing output and `pip freeze`.
- **Paleography details.** The 形聲 analysis of 虹 against a printed *Shuowen*, the 合集 numbers against the rubbings, and whether the chosen images are good representatives. I am not a specialist, and a paleographer should read section 4 before submission.
- **Upstream rights in HUST-OBC images** traced from 新甲骨文編, and arXiv's current licence options. Settle by asking the dataset authors and checking arXiv's licence page.
- **The Orascope selection script** is not in this repository. Settle by publishing it, or describe the selection criteria in the paper.
- **The Streamlit application** (paper line 129) was not run.