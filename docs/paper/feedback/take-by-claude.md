# Consolidated take on the external reviews

Reviews read: Qwen 3.8 Max, Z.ai GLM 5.3 High, ChatGPT, Opus 5.5 (section 7). Drafted 2026-10-11.
For each point I checked the claim against the repository where I could, and against the web where a reviewer named a
source. "Verified" below means I looked; "not verified" means I did not.

## 1. How much weight each review deserves

| Reviewer | Saw the repo? | Character of the review |
|---|---|---|
| Qwen | Yes, it cites file contents | Short, mostly positive, calls the paper ready. Two real findings (Pillow, related work); several "excellent" verdicts with no evidence. Its "ready" verdict I do not accept. |
| Z.ai | No, it says so | The most useful on the paper's wording and the paleography. Its code and licensing sections are, by its own account, checklists and not findings. Two of its guesses are wrong (see 3). |
| ChatGPT | No (could not clone), but it quotes the public `NOTICE` | Thorough and cautious; verdict "major revision". Strong on claims-versus-evidence, weak on specifics. Its Q7 asks for an end-to-end filename test that already exists. |

Useful side effect: ChatGPT read `NOTICE` on GitHub, so the repository is public and pushed.

## 2. Where all three agree (act on these)

| # | Point | My check | Verdict |
|---|---|---|---|
| C1 | "Manual work today", "none of it is tied to the data", "a function of the data", "generated and not made by hand" over-claim | True. The *layout* is generated; decompositions, glosses and glyph choices are still curated by hand, and `xpinyin` already adds pinyin automatically (verified: CTAN, LPPL, maintainer Liam Huang). | **Fix.** Say "layout generated from data", "no single tool lays out sound, shape and meaning together". |
| C2 | "Chinese characters began as pictographs" and "oracle bone script shows" is too strong | Z.ai: phono-semantic compounds already dominate the late Shang corpus (Qiu Xigui; Boltz). I agree it is an over-reading, and I wrote the sentence from your motivation. | **Fix wording, keep the motivation:** early Chinese writing, including oracle bone script, contains many pictographs. |
| C3 | "Modern characters have kept the sound and the meaning but lost most of the picture" | Sound and meaning have both changed over three thousand years. | **Fix or cut.** |
| C4 | The sentence "Reading 日 + 月 = 明 as sun and moon making bright, and 虫 + 工 = 虹 in the same way" breaks the no-etymology pledge | Correct, and it is the one sentence I would be embarrassed by. It places an interpretation next to a glyph the paper itself says does not look like a sun. | **Replace** with a neutral scope sentence (text in section 5). |
| C5 | Related work is too thin for arXiv | Correct. | **Add one paragraph**, only with sources I have verified (section 4). |
| C6 | MIT in the abstract needs qualifying | Correct: code is MIT, glyph images CC BY-NC 4.0, glosses CC BY-SA 4.0, fonts OFL. | **Qualify** in the abstract; put source and licence near the glyph figures, not only in the acknowledgements. |
| C7 | No evidence of benefit at scale | Correct. The paper shows six characters. | **Add a measured paragraph**: rebuild time for N characters after one data edit. I can run this today. |
| C8 | Subject class | Split: Qwen cs.CL or cs.DL, Z.ai cs.HC primary with cs.CL cross-list, ChatGPT cs.CL. Note your 2025 paper is physics.soc-ph (verified), so there is no precedent to follow. | **Your call.** I would take cs.CL primary, cs.DL cross-list. |

## 3. Reviewer claims that I checked and that do not hold, or are partly stale

- **Z.ai: "the `00README.json` key is `latex_compiler`".** Wrong. The [arXiv 00README page](https://info.arxiv.org/help/00README.html) lists `process.compiler` with `xelatex` as a supported value, which is what the file uses.
- **Z.ai and ChatGPT: the filename `u660e-pictmath-obs-zh.tex` is ambiguous.** It is only ever *constructed*, by Python and by `zitex.sty`, never parsed back, so a two-way parse cannot happen. A real collision needs a set or language name that itself contains a hyphen. Low risk. I would forbid `-` in set and language names and add one test.
- **ChatGPT: "the most valuable test is an end-to-end one".** It exists: `test_zimath_pict_keys_pick_the_right_snippet_in_a_real_document` compiles `\zimath`, `\zimath[pict]` and `\zimath[pict=obs]` in one document with XeLaTeX.
- **Qwen: "README should list Pillow".** Already added (`pip install -e ".[pict]"`). Qwen was reviewing before that.
- **Qwen: "emoji might render empty on arXiv".** No. The emoji PNGs are already in the tarball (`zitex-out/picts`), and arXiv compiles TeX only.
- **Z.ai: OFL Reserved Font Name for the font subset.** I checked the subset's metadata: copyright "© 2017-2022 Adobe", no licence or RFN field set. I could not confirm the RFN status of Noto CJK from the licence text, so the safe action is to ship `OFL.txt` with the font and the copyright line (section 5). Z.ai is right that loading by filename with `Path` is the robust route, and the paper already does that.
- **ChatGPT: the six glyph "reference images" it displays.** It says they are illustrative and not your files. Ignore them.

## 4. Real findings that nobody could have caught without the code, and one I found myself

1. **Bug (mine, found while checking Qwen's Pillow point): an emoji pict without Pillow fails loudly, not silently, and my documentation says otherwise.** `Lexicon.get_pict` checks that an emoji font exists but not that Pillow imports. If Pillow is missing, the snippet still names `picts/u….png`, `emoji_to_png` returns `False`, the file is never written, and XeLaTeX stops on a missing image. The design doc says an emoji "only counts when Pillow and a font are found". Fix the check and add a test.
2. **No build summary for missing pictures** (Z.ai, ChatGPT, Qwen all circle this). A character with no picture in a set, a failed emoji, and an unknown set name all give an empty cell with no message. Add a count to the build output ("set obs: 2 of 6 parts have no picture"), and a `--strict` that exits non-zero.
3. **Stale snippets** (Z.ai). `render --scan` overwrites, so a stale file is only possible if you skip the render step. Worth one sentence in the docs, not a hash.
4. **Code points above U+FFFF.** Both sides write lowercase hex with no padding, so it should work. Not tested; add one test with a CJK Extension B character.
5. **Overleaf** (Z.ai). Correct: no Python at compile time. The arXiv tarball already works that way. Say so: build locally, upload `zitex-out/`.

## 5. Action plan

**Status, 2026-10-11 (second pass):** items A1 to A9 are done in the paper (A5 uses only the sources I verified: `xpinyin`, EVOBC, HUST-OBC, cjkvi-ids; the rest are left as a TODO comment in `main.tex` for you to read first), A7 (the Pillow check, with a test) and A8 (`OFL.txt`, copyright line in `NOTICE`) are done, and `make-arxiv.sh` now regenerates the font subset and fails on a missing glyph. A10 is yours: the preview check on arXiv. Subject class: you chose physics.soc-ph, where your earlier paper was accepted; see section 8.

**A. Before submitting to arXiv (all text, plus two small fixes)**

1. Abstract and intro: rewrite C1 to C3 as in the table. Proposed opening: "Early Chinese writing, including the oracle bone script, contains many pictographs, and a character can be described by its sound, its shape and its meaning. Laying these out together consistently is repeated manual work."
2. Replace the C4 sentence in 4.1 with: "The figures juxtapose modern decompositions, dictionary glosses and selected oracle bone glyph images. These are separate records; placing them side by side does not establish a historical relationship between the modern components and the ancient forms."
3. Add a provenance line for the six glyphs, taken from `picts.csv` (for example 日 from `G_0773_前1.22.2合36169黃組`), and put "HUST-OBC, CC BY-NC 4.0" in the figure notes.
4. Qualify MIT in the abstract: "The code is released under the MIT licence; the bundled glyph images, glosses and fonts keep their own licences (see NOTICE)."
5. Related-work paragraph with: `xpinyin` (verified), EVOBC (verified: Guan et al., arXiv:2401.12467), HUST-OBC, cjkvi-ids and Unicode IDS (already cited). Reviewers also named `ruby`, Make Me a Hanzi, Hanzi Writer, CHISE, GlyphWiki, 小學堂, hanziyuan and Unihan. **I have not verified any of these**: I will check each URL and one-line description before it goes in, and leave out any I cannot confirm.
6. Fix the HUST-OBC bibliography entry. The arXiv page (verified) is titled "An open dataset for oracle bone script recognition and decipherment" and shows no journal reference. My entry says "character" and "Scientific Data, 2024", from your notes. The author list "Pengjie Wang et al." is correct (11 authors, verified). ChatGPT gives a Scientific Data DOI that I have not verified; add it only if you confirm it.
7. Fix the Pillow check (finding 1) and add its test.
8. Add `OFL.txt` and the copyright line to `docs/paper/arxiv/fonts/` and `NOTICE`.
9. Limitations: split into implementation limits (XeLaTeX only, no MathJax, overflow, Overleaf needs a local build, right-to-left untested) and data limits (curated by hand, 223 unconverted rows, six glyphs).
10. Re-run `./make-arxiv.sh`, read the arXiv preview PDF, then submit.

**B. Soon after**

- Build summary and `--strict` for missing pictures (finding 2); forbid `-` in set and language names; the U+FFFF test.
- A measured paragraph (C7): edit one lexicon entry, regenerate N characters, report time and files changed.
- A `requirements` list with versions, and a CI job that builds `examples/pict` and the arXiv tarball in a clean container.
- A compatibility table (XeLaTeX, pdfLaTeX, LuaLaTeX, MathJax, Overleaf) in the README.

**C. Later, only if the paper grows**

- A timed comparison with hand-made figures or a user study. Three reviewers want it; for a software note, one measured paragraph is enough.
- A calligraphy set and a larger set of chosen glyphs.

## 6. Where I would push back

- **Do not cut the reaction metaphor** (Qwen's cut 2). It is the paper's core idea and its title. ChatGPT's softer fix is better: say it is a representation of the chosen decomposition.
- **Do not drop the oracle bone motivation.** Reword it as above. It is your reason for the picture row, and Z.ai itself says the sound, shape and meaning framing stands without it, which makes a short version safe.
- **Do not claim "ready for arXiv" from Qwen's verdict.** Z.ai and ChatGPT are right that the wording issues come first, and they are cheap to fix.
- **Do not add an etymology interpretation to answer the paleography comments.** Z.ai notes that 工 is generally read as the phonetic part of 虹, which contradicts the folk reading. The safest course, which also follows the paper's pledge, is to say nothing about why the parts are what they are.

## 7. Opus 5.5 (read in full, 2026-10-11)

Verdict: "not ready for arXiv yet, though close". It reviewed commit `879a19b`, so some points are already done (tone-down edits, Pillow check, `OFL.txt`, related-work paragraph, `make-arxiv.sh` failing on a missing glyph). It ran the code: 347 tests passed, every paper snippet rebuilt byte for byte, the tarball compiled clean. It is the only review that did so, and I weigh it highest.

**Checked by me against the repo (confirmed, not yet fixed)**

- `--scan` uses the first `-l` language when a call has no `lang=` (`cli.py:219`), while the package asks for `en`. With `-l zh` this writes the wrong file and XeLaTeX prints a red mark.
- `scan_tex` does not strip spaces inside `[pict = obs, lang = zh]` (`build.py:62`), so the two sides name different files.
- `db-build --in-place` writes into the source database, so the paper's "the source database is never modified" (main.tex line 68) is wrong as written. The CLI's own help for the input says "never changed".

**Not checked by me:** the other code findings (a pict value that is neither a file nor a drawable emoji stops XeLaTeX with exit 0; a missing picture file is dropped silently; `日 = 日` for leaf characters; `merge_file` crash on an empty entry; `ZITEX_EMOJI_FONT` ignored unless its name contains "emoji"; `fc-match` run per call; `compile_pdf` discards the log). Each has a reproduction in the review.

**New items beyond the first three reviews, in order of weight**

1. **Paper, 虹.** 工 is the sound part (形聲), so "in the same way" and the 🐛 + 🛠️ = 🌈 figure assert a wrong etymology. Opus's fix: render 虹 with `arrow=role` ("sound: gōng"), which zitex already supports. This agrees with Z.ai and strengthens my section 6 last bullet: saying nothing is not enough, and the example itself should show the role.
2. The oracle bone 虫 is a snake (虺) and the 虹 glyph is a whole drawing, not 虫 + 工. Add one sentence that an ancient form need not contain the ancient forms of the modern parts.
3. Glyph provenance: 月 comes from HWOBC, a handwritten collection, not an inscription; 日 is from a late group and 明 and 工 from an early one. List 合集 number or "HWOBC (handwritten)" per glyph, and prefer an inscription glyph for 月.
4. "Modern characters have kept the sound and the meaning" and "originated as pictographs": same as C2/C3, now with sources (Baxter and Sagart 2014; Qiu Xigui 2000; Boltz 1994). I have not read these.
5. Row of pictures is not "shape" (the character row is). Rename it.
6. **Licence of the paper itself:** the glyph figures are CC BY-NC, so do not release the arXiv paper under CC BY or CC BY-SA; use arXiv's default licence or CC BY-NC-SA. I did not check arXiv's menu. Add per-folder `LICENSE` files for the image folders.
7. Title over-claims ("does not decompose, it typesets decompositions"). Suggestion: "Typesetting Chinese Character Decompositions from Data with zitex".
8. Radical rule as described (main.tex 88-89) is not what the code does (a right-side radical goes to `R`; two Kangxi radicals, as in 明, give `L-R`).
9. Related work: more names (cjk-decomp, BabelStone IDS, Make Me a Hanzi, CUHK Multi-function Database, Sears's hanziyuan, mhchem/chemfig, the Unicode 15.1 IDS operators). Opus says it checked the URLs; I have not. Your reading list.
10. Reproducibility: xeCJK is missing from a basic TeX Live (`texlive-lang-chinese` on Debian); Pillow was missing from `pyproject.toml` extras (now added); emoji PNGs differ by font version, so pin or record the font in the manifest; the glyph-selection script lives in Orascope; `quarantined` is 223 in `zx_meta` but 222 rows in `zx_quarantine` (so the paper's 223 needs a check).
11. Web: KaTeX rejects the `pictmath` column spec and MathJax would print the `\parbox`, so the picture view has no web form. Say so, or add a plain variant.
12. Design suggestion: have the package write the snippet names it needs to `\jobname.zitex` and let Python read that, replacing the regex scanner. This removes scanner/package disagreement for good. Larger change; worth it only if you keep developing the tool.
13. Stale arXiv tarball in git and `make-arxiv.sh` not regenerating `zitex-out/`; pin the Noto version in `fonts/README.txt`.
14. Writing: three repeated points, the "Readings" paragraph describes an unshown feature, overfull line (16 pt), three sentences to cut. The sceptical question: what does this give over twenty lines of `\overset` macros, and has anyone else used it? Opus suggests one 30 to 50 equation handout as the answer (this is my C7 with a concrete form).
15. Subject class: Opus says cs.DL primary, cs.CL cross-list. Four reviewers, no agreement; your physics.soc-ph choice stands (section 8).

**Contradicts me or the others**

- Opus says the six failing tests on your machine did not fail for it (Streamlit missing, UI tests skipped). That points at your environment; I still have not looked at them.
- Qwen and Z.ai praised the "no interpretation" wording around 虹; Opus shows the paper does interpret (line 176 and the emoji figure). Opus is right.
- Opus supports my correction that `00README.json` with `process.compiler` is accepted.

**Status after the Opus pass (2026-10-11, while you were away)**

Done in code (`src/zitex`, tests in `tests/test_pict.py`):
- `--scan` defaults to `en` as the package does; option spaces are stripped (`[pict = obs, lang = zh]`); both have tests.
- A picture that was asked for and cannot be made (a missing file, a word like `sun`, no emoji font or Pillow, a failed emoji) is reported and no longer promised to XeLaTeX; the build prints the problems and the parts that have no picture, records `parts_without_pict` and `picture_problems` in `build_manifest.json`, and `render --strict` exits non-zero.
- A leaf character is one column (no `日 = 日`); `pinyin=False` no longer prints the result's pinyin; an empty lexicon entry is skipped; `ZITEX_EMOJI_FONT` is accepted whatever its file name; `fc-match` is cached; a failed XeLaTeX compile prints the log tail; hyphens in set and language names are refused; a test covers a code point above U+FFFF.
- `db-build --in-place`: help text and the paper now say it is opt-in. The `render` command was registered as `render-cmd` (Click 8.1 does not strip the suffix); it is now named `render` explicitly.

Done in the paper (`docs/paper/arxiv/main.tex`): new title; 虹 kept but with no claim about sound or meaning (the role arrow was tried and removed, at the author's request: the paper takes no side on which part carries the sound); a sentence says the equations are not a sum of glosses and that sources differ; the ancient form of a whole character need not contain those of its parts; a note that glosses are those of the modern characters; a "kind of source" column in the glyph table (月 is a handwritten copy); the radical rule as implemented; the picture row described as "a picture", not "shape"; a measured section "Cost of a correction"; the unshown "Readings" paragraph tied to the 虹 example; repeated XeLaTeX/MathJax sentence cut; "about 220" unconverted rows (the database says 223 in `zx_meta` but holds 222 rows).

Done in packaging: `benchmarks/handout.py` (59 equations: 0.08 s render + 0.41 s XeLaTeX, 59 of 59 snippets changed by one edit, stable over three runs); `make-arxiv.sh` regenerates the snippets with `--strict` before packing (no `--arrow role` any more); `LICENSE` files (CC BY-NC 4.0) in the three image folders; `build.sh` checks for `xeCJK.sty`; README names the Debian packages; the `etymology` keyword is gone.

**Your six (now seven) failing tests, explained.** Two causes on your machine, neither in my edits: (1) `python -m zitex` is spawned by the pipeline tests and the package is not installed in your Anaconda Python, so they fail unless you run `pip install -e .` or `PYTHONPATH=src pytest`; with `PYTHONPATH=src`, 361 pass. (2) The seven `test_ui.py` failures come from Streamlit 1.32.2 rejecting `width="stretch"` in `st.data_editor` ("'str' object cannot be interpreted as an integer"); they need a newer Streamlit. Opus's environment skipped them.

**Not done, your call or later**
- Related-work additions (Make Me a Hanzi, CUHK database, cjk-decomp, BabelStone, mhchem): not read by me.
- Baxter and Sagart, Qiu Xigui, Boltz for the pictograph wording. A paleographer should read section 4.
- arXiv licence for the paper itself (not CC BY or CC BY-SA, because of the NC glyphs).
- Emoji font name and version in `build_manifest.json`; pinning the Noto version in `fonts/README.txt`.
- The `\jobname.zitex` job-file design, a web (HTML) form of the picture view, the glyph-selection script (Orascope), the tarball in git going stale, `pyproject.toml` `Paper` URL (still the model paper), `db/NOTICE.md` entries for `zitex-orig.sqlite3` and the review CSVs.

## 8. Subject class: physics.soc-ph

The three reviewers suggested cs.CL, cs.HC or cs.DL, and I leaned cs.CL; none of us weighed that your earlier paper (arXiv:2502.19428) is physics.soc-ph. Your choice is reasonable: it keeps the two papers together. Two cautions. arXiv moderators decide the final category and may move a paper they think off-topic, and a typesetting tool is further from physics.soc-ph than your analysis of the writing system was. If the paper is moved, nothing in the source changes. A cross-list to cs.CL or cs.DL is optional and costs nothing; it is your call.
