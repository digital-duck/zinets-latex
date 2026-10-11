# Peer review: "Decomposing Chinese Characters: LaTeX Typesetting with zitex"

**Important caveat up front:** I could not access the repository, so I could not run `examples/pict/build.sh`, `make-arxiv.sh`, or read `lexicon.py`, `render.py`, `build.py`, `zitex.sty`, or `NOTICE`. Questions 5, 6 and 7 are answered from the paper text only, and everything I could not check is listed at the end. Do not treat those sections as findings about the code — treat them as the checklist you must run before submitting.

---

## Verdict

zitex makes a real, well-scoped contribution: a data-driven pipeline that turns character decomposition records into aligned sound–shape–meaning figures in XeLaTeX, with a clean Python/LaTeX split and a sensible opt-in picture view. The paper is **not ready for arXiv as it stands**: the introduction's paleographic framing is contestable, the central "this is manual work today" claim is asserted rather than demonstrated and is contradicted by existing tools the paper does not cite, and the one sentence interpreting 明 and 虹 ("sun and moon making bright… in the same way") breaks the paper's own no-etymology pledge. The single most important fix: rewrite the abstract and first two paragraphs so every claim matches what the artefact demonstrates, and delete or neutralise the interpretive reading of 明/虹 in §4.1.

---

## 1. Claims against evidence

**Important — "Presenting the three together and consistently is manual work today… none of it is tied to the data behind it" (Abstract, sentences 3–4).**
Only asserted, and partially *contradicted*: LaTeX packages such as `xpinyin` already place pinyin over characters automatically from a database (see Q3). What is genuinely manual is the *combined* sound+shape+meaning layout and the decomposition figures. Fix: qualify to "no single tool lays out sound, shape and meaning together", and name the tools that do part of the job.

**Important — "makes the figure a function of the data" (Abstract).**
Demonstrated for *layout* (§4 shows four views generated from records), but the *content* is hand-curated: §4.1 says the glyphs are "one chosen glyph per character" chosen by the author, and §5 admits glosses "are first senses from a dictionary and are not curated". The figure is a function of a manually curated lexicon. Fix: say "the layout is a function of the data".

**Important — "generated and not made by hand" (Intro, end of ¶3).**
Same problem. The claim is true for placement and false for content. A sceptical reader will read this as "no manual curation", which the paper itself refutes two pages later. Fix: "generated, not laid out by hand".

**Important — "every character has a sound, a shape and a meaning" (Abstract, sentence 2).**
"Every" is over-claiming: reconstructed readings and senses are disputed for many characters, particularly oracle bone characters. Fix: drop "every".

**Minor — "consistently" (Abstract, "Presenting the three together and consistently…").**
Demonstrated on six showcase characters. At scale the paper reports 223 of ~6,200 rows that "cannot be converted yet, and warnings remain". Fix: either qualify ("a consistent layout, applied wherever the data converts") or add an auto-generated appendix of hundreds of characters as evidence.

**Minor — "A short LaTeX package only includes those snippets" (Abstract, last-but-one sentence).**
Asserted; no metric given. Fix: one clause with the line/file count of `zitex.sty`.

**Demonstrated (no action needed):** the four views exist and are shown (§3, §4); rows line up across parts (§4.1); named readings avoid duplicating data (§3); missing files degrade to a warning and a red mark (§3); per-language meaning rows (§4.1).

---

## 2. Oracle bone script statements

**Important — "Chinese characters originated as pictographs" (Intro, sentence 1) and "Chinese characters began as pictographs, as the oracle bone script shows" (Abstract, sentence 1; repeated at start of §4.1 "Oracle bone glyphs").**
A paleographer would challenge this directly: by the late Shang, the oracle bone corpus is a mature writing system in which phonosemantic compounds (形声字) already dominate; pictographs are a minority even in the earliest attested material (Qiu Xigui, *Chinese Writing*; Boltz, *The Origin and Early Development of the Chinese Writing System*). "The oracle bone script shows" that characters *began* as pictographs is exactly the over-reading the paper promises to avoid. Fix: "the earliest attested Chinese characters include many pictographs" — or simply start from the sound/shape/meaning framing, which needs no origin story.

**Important — "Reading 日 + 月 = 明 as sun and moon making bright, and 虫 + 工 = 虹 in the same way, gives:" (§4.1, sentence before the emoji figures).**
This is the sentence that breaks the no-etymology pledge, twice: (a) for 虹, 工 is generally analysed as the phonetic component, and "in the same way" equates a (contested) semantic-compound reading of 明 with a phonosemantic structure — "insect work rainbow" is a folk reading, not "the data"; (b) the paper itself notes that the chosen 明 glyph is "a crescent next to a small box and not a sun and moon", so the "sun and moon making bright" gloss is an *interpretation* placed directly beside the ancient form it contradicts. Fix: replace with something purely structural, e.g. "With the modern decompositions 日+月 and 虫+工, the picture view gives:".

**Important — "Modern characters have kept the sound and the meaning but lost most of the picture" (Intro, ¶1, last sentence).**
Specialists would challenge "kept the sound": the sound has changed beyond recognition from Old Chinese to modern pinyin, and meanings have shifted too. Fix: "kept a sound and a meaning, though both have changed, and lost most of the picture".

**Minor — "the sun is a circle, the moon a crescent, and a creature or a tool is drawn as what it is" (Intro, ¶1).**
Acceptable simplification for 日 and 月; "a creature or a tool is drawn as what it is" is too broad for the OBC corpus. This sentence disappears if you take the fix above.

**Minor — "明 is a crescent next to a small box" (§4.1).**
Handled well: the paper declines to identify the box (many scholars read it as 囧 'window'), which is consistent with the no-interpretation stance. No change needed; optionally add "we do not identify it".

**Kept to the pledge elsewhere:** "a modern decomposition and an ancient glyph are separate records… without interpreting either" (§4.1) and "We make no claim about the etymology of any character" (§5) are exactly right — the violations are the sentences above, not these.

---

## 3. Related work — what is missing

Severity for this whole question: **important** (the paper admits the gap, but "we did not survey other tools" does not excuse claims that other tools contradict).

Specific things a reviewer will expect, each with what the paper must say:

- **`xpinyin` (CTAN, https://ctan.org/pkg/xpinyin)** — automatically annotates Chinese text with pinyin above the characters in XeLaTeX, from a built-in database. This directly contradicts "pinyin and glosses are placed by hand". One sentence: pinyin annotation is solved; what remains unsolved is the combined decomposition + picture layout.
- **`ruby` (CTAN, https://ctan.org/pkg/ruby)** — generic ruby annotation above/below base text; the paper's meaning/pinyin rows are ruby-like. Say why stacked ruby does not achieve the aligned multi-part grid.
- **Hanzi Writer (https://hanziwriter.org)** and its data **Make me a Hanzi (https://github.com/skishore/makemeahanzi)** — JavaScript library that animates and draws characters from stroke data. Related to "shape", web-based, not LaTeX. One sentence of scope comparison.
- **CHISE / CHISE IDS find (http://www.chise.org/)** — long-running project distributing component decompositions and glyph composition data. Must be discussed alongside cjkvi-ids [2].
- **GlyphWiki (https://glyphwiki.org)** — composes and *renders* glyphs from components on the fly; the closest existing thing to "shape generated from decomposition data". Needs a sentence: it renders the glyph, not a sound/shape/meaning layout, and it is a web service.
- **小學堂 (Xiaoxuetang, Academia Sinica, https://xiaoxue.iis.sinica.edu.tw)** — a well-known glyph-evolution database including oracle bone forms per character. This is precisely the resource the `pict=obs` row imitates; the paper should say how its per-character, hand-chosen glyph files relate to such databases. (I am unsure of its current licence terms — check before citing.)
- **Unihan database (https://unicode.org/charts/unihan.html)** — radical–stroke indices and other decomposition-adjacent data; the radical rule in §2 should be situated against it.
- **pypinyin (https://github.com/mozillazg/python-pinyin)** — if the pinyin/lexicon pipeline derives from CC-CEDICT, state which tool produced it.
- Richard Sears' Chinese Etymology site (https://hanziyuan.net) and 殷契文淵 (http://jgw.aynu.edu.cn) — plausible additions for glyph-evolution resources; I am unsure of their current availability/licences, so verify before citing rather than taking my word.

What the paper would need to say about each, in most cases, is one sentence of scope: what the tool does, and which of the three dimensions (sound / shape / meaning) and which of the views (equation / matrix / tree / picture) it covers. That is roughly one added paragraph, and it converts "we did not survey" from an admission into a defensible position.

---

## 4. Design

**One `array` grid instead of stacked `\underbrace` — good decision (§3, "Pictures").**
The paper's central claim is aligned rows across parts; underbraces cannot align rows between different parts. Consequences: column widths are natural-width, so one long meaning inflates the whole column (the known overflow limit), and RTL glosses would come out left-to-right because the column order is fixed. The grid is the right call; document the RTL limitation. Severity: minor.

**`pictmath` as a separate opt-in style — good decision, but the API surface is muddled.**
The paper shows `\zimath[pict]{字}`, `\zimath[pict=obs]{字}`, and calls the style `pictmath` in §3/Q7's snippet names. Three spellings for one concept (`pict`, `pict=obs`, `pictmath`) is a discoverability hazard and a sty/Python drift risk. Fix: one key taking set names, `pict=emoji|obs|…`, documented in one place. Severity: important (for the tool's usability; minor for the paper).

**Pictures per character from named sets — sound design, two failure modes.**
(i) Silent empty cells: "a part with no glyph in the set has an empty cell" — a user cannot tell a missing glyph from a deliberate omission without reading logs. Fix: a build summary ("set obs: 3 of 5 parts missing a picture"). (ii) It does not scale: per-character hand curation is the bottleneck the paper honestly flags; set-level sources (Xiaoxuetang-style databases) are the natural fix. Severity: important for the tool, already disclosed in the paper.

**Emoji rasterised to PNG at build time — the weakest of the four decisions.**
Hidden build-time dependencies (Pillow + a colour-emoji font, both platform-dependent); **Overleaf users cannot run this step at all**, since Overleaf does not execute arbitrary Python during compilation — they must build snippets locally and commit the PNGs, which the paper does not say; fixed-resolution PNGs will blur or mismatch at other font sizes; and the rasterised emoji add binary assets and a font-licence question to any arXiv bundle. An SVG/PDF-vector path (or a documented "commit the built folder" workflow) would serve the same goal. Severity: important.

**For whom it breaks, beyond the known limits:** Overleaf (no Python at compile time, emoji-font availability); LuaLaTeX users (excluded, known); arXiv (snippets and PNGs must all be shipped, since arXiv runs TeX only — see Q5/Q9); RTL glosses (array column order); very wide equations (known).

---

## 5. Reproducibility

I could not run or read the build scripts — everything here is inferred from the paper, and none of it is verified.

**Blocker (if confirmed) — the §4 figures depend on assets and data whose presence in the repository I cannot confirm.** The oracle bone PNGs (`u<hex>.png`, "a handful chosen by the author") and the lexicon files must be in the repo for anyone to rebuild Figures 2–3 and the §4.1 equations; the full decomposition database is known not to be. If the shipped `zitex-out/` snippets are not in the repo, the §4 figures are not reproducible from the repository alone. Fix: commit the generated snippets and image files used by the paper (or a script + data that regenerate them byte-for-byte), and say in the paper which path was used.

**Hidden dependencies to document, from the paper's own description:** a Python version (unspecified), PyYAML, SQLite (stdlib), **Pillow and a colour-emoji font** for the PNG rasterisation, Noto Serif CJK SC, HUST-OBC images, and the CC-CEDICT-derived lexicon. Fix: a `requirements.txt` with versions, a Dockerfile or CI workflow that builds the paper end-to-end, and a statement in §4 of the exact commands and environment.

**Minor — §4's example commands are incomplete.** The three-line workflow at the top of §4 (`setup`/`extract`/`xelatex`) does not include the `render … --scan` invocation shown in §4.1, so a reader following §4 top-down cannot reproduce the picture view. Fix: one consolidated reproducible sequence.

---

## 6. Licensing and data

I could not read `NOTICE`; comments are about the paper's statements and standard practice.

**Important — "zitex is released under the MIT licence" (Abstract, end) is misleading as a description of the repository.** Mixing CC BY-NC images into an MIT code repository is legal and common *if* the licences are per-file and clearly separated (images directory, data directory, `NOTICE`), but the repository as a whole is then not MIT, and a README/abstract that says "MIT" without qualification invites accidental commercial reuse of the NC images. Fix: state the mixed structure wherever "MIT" appears: "code: MIT; glyph images: CC BY-NC 4.0 (HUST-OBC); gloss data: CC BY-SA 4.0 (CC-CEDICT); fonts: SIL OFL."

**Important — attribution for the HUST-OBC images should be in the figure captions, not only in the acknowledgements.** CC BY-NC 4.0 requires attribution "appropriate to the medium"; in a paper, that means at (or near) Figures 2–3 and the §4.1 glyph equations. Fix: add the source and licence to each caption.

**Important — the CC BY-SA 4.0 gloss data creates share-alike obligations on those files specifically.** That is compatible with MIT code per-file, but the `NOTICE` (which I cannot check) must say that adapted gloss files must remain BY-SA. arXiv submission under the arXiv non-exclusive licence or CC BY is fine for the *paper text*; the BY-SA data files inside the source package remain BY-SA.

**Important — the font subset in the arXiv source.** Shipping an OFL font with the submission is permitted, provided `OFL.txt` and the copyright header travel with it. The trap is the Reserved Font Name: a *subset* is a modified version, and OFL's RFN clause means a modified font must not be distributed under the reserved name ("Noto…") — and the arXiv build must then load it by *filename*, not family name, since arXiv's TeX installation may not have Noto Serif CJK SC. I am not fully certain how the OFL FAQ treats subsetting-for-embedding in current practice; check it, and either rename the subset + `\setmainfont[Path=./fonts]{…}` or confirm the exemption. (Verified practice: loading by filename with `Path` is the robust route for arXiv either way.)

**Acceptable with caveats — CC BY-NC images on arXiv.** arXiv's distribution is non-commercial and this is generally accepted, but say in the paper (as §5 does) that the images are excluded from the MIT licence, and note that commercial reusers of the arXiv source cannot reuse those PNGs.

---

## 7. Code quality

I could not read the four files, so I cannot report bugs. Below is what the paper's own description of the interface makes fragile — treat each as a checklist item, not a finding.

**Filename grammar is ambiguous (§3, "The only interface between the two halves is the file name of a snippet, `u<hex>-<style>[-<lang>][@reading].tex`").** With a style like `pictmath-obs` (implied by `u660e-pictmath-obs-zh.tex`) and an optional `-<lang>`, `u660e-pictmath-obs-zh.tex` parses two ways (`style=pictmath-obs`, `lang=zh` vs `style=pictmath`, `lang=`obs-zh`) — unless the package enumerates styles and languages, the Python writer and `zitex.sty` reader can silently disagree. Fix: forbid `-` in style and lang names, or use a separator styles cannot contain, and unit-test the round-trip in both directions. Severity: likely important.

**Hex canonicalisation.** Code points above U+FFFF (CJK Extension B+) give five-digit hex; upper/lowercase and zero-padding must be fixed on both sides or lookups fail intermittently. Severity: minor if already handled.

**Stale-snippet risk.** The filename carries no content hash, so a snippet generated from an old lexicon can be silently `\input` after a data revision. If `render --scan` always regenerates, say so in the docs; a `--strict`/`--clean` mode would settle it. Severity: important if unguarded.

**Silent failure modes to enumerate tests for:** missing picture → empty cell (no per-figure signal); missing font → boxed code point with a warning buried in the log; missing snippet → warning + red mark (good, but count them in a build summary). Suggested tests: filename round-trip, pict-row fallback order (image → emoji → nothing), gloss fallback order (gloss → concept → category → nothing), lang fallback, font-resolution order, and the radical-rule validation warnings.

---

## 8. Writing

**Important — the manual-work paragraph is duplicated.** Abstract sentence 3–4 and Intro ¶3 say nearly the same thing ("pinyin and glosses are placed by hand, pictures are pasted and aligned…"). Cut the intro copy and replace it with the tool citations from Q3.

**Important — §4.1 is repetitive.** Three nearly identical equations are shown for emoji (en, zh) and then two more for oracle glyphs; the point is made after two. One emoji equation + one obs equation, plus a sentence noting the language key, carries the same information.

**Minor — §2 is opaque on first reading.** The pattern→IDS-operator mapping sentence ("for instance L-M and L-R map to… Mo-D, Mo-U, Mo-R and Mo-M map to the surrounding operators") and the radical rule ("a Kangxi radical is peripheral, so the radical is placed at L and the other part at M") are each one dense sentence doing a lot of work; the 器 pattern LU-RU-M-LD-RD is named before any reader has seen what it means. Fix: one worked example per idea.

**The three sentences I would cut first:**
1. Intro ¶1, sentences 1–2: "Chinese characters originated as pictographs. The oracle bone script, carved on turtle shells and animal bones in the late Shang dynasty more than three thousand ago, still shows the pictures: the sun is a circle, the moon a crescent, and a creature or a tool is drawn as what it is." (Contested, and the paper does not need it — the sound/shape/meaning framing stands on its own.)
2. §4.1: "Reading 日 + 月 = 明 as sun and moon making bright, and 虫 + 工 = 虹 in the same way, gives:" (Breaks the no-interpretation pledge; see Q2.)
3. Intro ¶3, sentences 2–3: "Pinyin and glosses are placed above and below the characters by hand, pictures are pasted and aligned one by one, and the decomposition is drawn in a graphics program or in TikZ." (Duplicates the abstract; replace with the related-work paragraph from Q3.)

**The question a sceptical reader will ask that the paper does not answer:** *what does this actually save, and at what scale?* The paper claims manual work is "slow to produce… and must be redone", but shows no end-to-end comparison — not even one figure's time by hand vs. by zitex, nor a batch beyond six characters. One paragraph with a timed rebuild of, say, 100 characters after a data revision would answer it.

---

## 9. arXiv readiness

**Important — the font is the main failure risk.** If the document selects Noto Serif CJK SC by *family name*, the arXiv build fails (I am not confident the font is in arXiv's TeX installation); if the bundled subset is renamed per the OFL RFN issue (Q6), family-name lookup fails too. Fix: bundle the font file and load it by filename with `Path`, and test the tarball on a machine without Noto installed. Also check the subset's size against arXiv's file-size limits (full Noto CJK weights are far too large; a subset should fit, but I am unsure of the current limits — verify).

**Important — all generated assets must be in the tarball.** arXiv runs TeX only, never the Python pipeline: every snippet (`zitex-out/…`), every PNG (emoji and oracle glyphs), the font, and `OFL.txt` must be flattened into the source with paths that still resolve after `make-arxiv.sh` flattens directories. A single missing directory rename breaks every `\input`.

**Minor — version skew.** arXiv's TeX Live is frozen annually; `xeCJK` and `TikZ` behaviour differences are unlikely to break this document, but the only real check is a test upload.

**Minor — `00README.json` selecting XeLaTeX is the correct mechanism** (I cannot verify the file's key syntax; the standard is a `"latex_compiler"` entry).

**Subject class:** `cs.CL` is the weakest fit and `cs.DL` (digital libraries) is a poor fit. I would submit **primary `cs.HC`** (document/reading interfaces, pedagogy of writing systems) with a **cross-list to `cs.CL`** (precedent: computational work on Chinese characters and oracle bone decipherment appears there). If the paper were reframed around the notation and data model rather than the tool, a `cs.CL` primary would become defensible. I am genuinely uncertain here; check where comparable glyph/decomposition papers landed.

---

## Not verified

- **Repository contents and build:** could not run or read `examples/pict/build.sh`, `docs/paper/arxiv/make-arxiv.sh`, `00README.json`, or any source file; running both scripts on a clean machine with only the repo cloned would settle §5 and most of §7.
- **`NOTICE` correctness and sufficiency:** could not read it; a licence audit (e.g., `licensecheck` or a manual per-directory pass) would settle §6.
- **Snippet-name agreement between `zitex.sty` and Python:** the `u660e-pictmath-obs-zh.tex` ambiguity in §7 needs one look at both parsers to confirm or dismiss.
- **The OFL subsetting / Reserved Font Name question:** I am unsure how OFL 1.1 practice treats subsets; read the OFL FAQ section on subsetting before deciding whether to rename the bundled font.
- **arXiv file-size limits and Noto Serif CJK SC availability on arXiv's TeX Live:** both change over time; check arXiv's current help pages.
- **Availability/licences of Xiaoxuetang, hanziyuan.net, and 殷契文淵** (Q3): verify URLs and terms before citing.
- **The HUST-OBC citation details ([3]) and the author's prior paper [1]:** not checked against the sources.
- **Whether Overleaf's environment includes a colour-emoji font** for the PNG pipeline: needs one test build on Overleaf.