# Peer review: “Decomposing Chinese Characters: LaTeX Typesetting with zitex”

Overall verdict: Major revision required before arXiv submission.

The paper presents a useful, concrete typesetting tool: it turns structured Chinese-character decomposition data into several consistent LaTeX representations, including an optional picture view that aligns pronunciation, character components, meanings, and images. The draft explains the architecture and demonstrates the intended output, but it does not yet substantiate several broad claims about existing practice, historical writing, or the benefits of the approach; I also could not execute the repository's build scripts or inspect all source files in this review. The single most important fix is to separate what zitex demonstrably automates from what its input data merely asserts, then revise the historical examples and abstract accordingly.

## 1. Claims against evidence

The assessment below distinguishes direct evidence in the six-page PDF from statements that would require external evidence, user studies, benchmarks, or further implementation testing. A claim that is “demonstrated” is supported by the examples shown; this does not necessarily mean it has been independently verified.

### 1.1 Abstract

Location: Abstract, PDF p. 1, lines 9–21.

| Claim                                                                                                                 | Assessment                                                                                                                                                                                        | Severity and concrete fix                                                                                                                                               |
| --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| “Chinese characters began as pictographs”                                                                             | Overgeneralized historical claim. The history of Chinese writing includes multiple character-formation principles and cannot be summarized as every character originating pictographically.       | Important. Replace with a qualified statement: early Chinese writing includes pictographic signs, while character formation and historical development are more varied. |
| “every character has a sound, a shape and a meaning”                                                                  | Useful organizing model, but not literally universal: pronunciation and meaning can depend on context, and characters can have multiple readings and functions.                                   | Minor. Say “we represent each character through its shape, pronunciation(s), and gloss(es).”                                                                            |
| Presenting these three consistently “is manual work today”                                                            | Unsupported universal claim about current practice. Existing annotation and diagramming tools may automate parts of this task.                                                                    | Important. Narrow it to “often requires manual layout or tool-specific workflows,” and support it with a comparison of existing tools.                                  |
| Pinyin and glosses are placed by hand; pictures are pasted and aligned; decompositions are drawn in graphics software | Anecdotal generalization presented as fact. No survey or examples establish how common this workflow is.                                                                                          | Important. Describe it as the workflow zitex is designed to replace, or document representative workflows and their limitations.                                        |
| “none of it is tied to the data behind it”                                                                            | Too absolute. Some existing tools are data-driven.                                                                                                                                                | Important. Say that zitex generates its figures from a structured character record and explain the specific consistency advantage this provides.                        |
| zitex “makes the figure a function of the data”                                                                       | Partly demonstrated. The paper describes structured entries and generated snippets, but does not show an edit-and-regenerate experiment or establish that all visual properties are data-derived. | Important. Use “generates figures from structured data and rendering settings.” Include a reproducible before/after example.                                            |
| A character is a short entry containing decomposition and positions                                                   | Demonstrated as the proposed representation, although the paper does not provide a complete schema specification.                                                                                 | Minor. Show a compact schema example and distinguish character facts from rendering metadata.                                                                           |
| Python validates the data and writes self-contained snippets for multiple views                                       | The architecture and output examples support this. The limits section also reports unresolved database conversions and warnings.                                                                  | Minor. Specify which checks are implemented, which are warnings, and what “self-contained” includes and excludes.                                                       |
| A picture view lets each part show sound, shape and meaning in aligned rows                                           | Demonstrated by the examples in Section 4.1. The claim is about layout, not the historical correctness of the data.                                                                               | Minor. Retain, but say “can display” because data fields and pictures may be missing.                                                                                   |
| The LaTeX package is short and only includes snippets                                                                 | Supported by the architecture description, but the package's size and maintainability are not quantified.                                                                                         | Minor. State the design intention rather than imply a measured advantage.                                                                                               |
| The work describes notation, design, fonts, and source database                                                       | Demonstrated by the paper's organization.                                                                                                                                                         | No substantive fix needed.                                                                                                                                              |
| zitex is released under MIT                                                                                           | The repository identifies the code as MIT-licensed, but the same license does not apply to all bundled assets.                                                                                    | Important. Qualify the statement: “The code is MIT-licensed; bundled data, images and fonts retain their respective licenses.”                                          |

### 1.2 Introduction

Location: Section 1, PDF pp. 1–2, lines 25–53.

| Claim                                                                                      | Assessment                                                                                                                                                        | Severity and concrete fix                                                                                                                                         |
| ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Oracle bone script “still shows the pictures”                                              | Overgeneralizes the relationship between ancient glyphs and depicted objects. Many signs are not straightforward pictures, and interpretation can be disputed.    | Important. Say that some oracle bone forms have pictographic features; identify each displayed glyph by source and label.                                         |
| “the sun is a circle, the moon a crescent”                                                 | A simplified visual interpretation presented as a general historical fact. The particular glyphs and their variants are not documented here.                      | Important. Describe the actual selected images rather than asserting canonical forms. Include dataset identifiers and source-image references.                    |
| “a creature or a tool is drawn as what it is”                                              | Overstates transparency of ancient signs and assumes their referents are unambiguous.                                                                             | Important. Remove or qualify this sentence. Explain that some forms are pictographic but not necessarily self-interpreting.                                       |
| “Modern characters have kept the sound and the meaning but lost most of the picture”       | Historically misleading as a general account. Character forms, pronunciations and meanings have all changed; many modern characters are phono-semantic compounds. | Important. Replace with a narrower observation about the visual transformation of selected characters.                                                            |
| Teachers and researchers keep placing ancient glyphs next to modern characters             | Plausible, but no examples or references support the claimed practice or its frequency.                                                                           | Minor. Cite a representative teaching resource or corpus, or remove “keep.”                                                                                       |
| Papers and teaching material need all three dimensions for each component and character    | A statement of motivation, not an established general requirement.                                                                                                | Minor. Frame this as the use case zitex targets.                                                                                                                  |
| Manual work is slow, inconsistent and must be redone when analysis changes                 | Plausible, but the paper gives no baseline, time measurements, or comparison.                                                                                     | Important. Present this as a problem hypothesis; a small case study comparing manual and generated figures would strengthen it.                                   |
| “generated and not made by hand”                                                           | Overstates automation. The decomposition, readings, glosses, and choice of glyphs can still require manual decisions.                                             | Important. Change to “layout is generated from data, while the underlying annotations remain subject to human review.”                                            |
| A character can be read as a reaction, such as 亻 + 弗 → 佛                                   | Demonstrated as the tool's chosen representation, but the equation metaphor should not be confused with a complete historical or linguistic analysis.             | Minor. Label it explicitly as a representation of the selected decomposition.                                                                                     |
| The representation is used for teaching, studying organization, and computational analysis | Cites reference [1], which is the author's own earlier work. The breadth of the claim is not established by that citation alone.                                  | Minor. Add independent references or narrow the statement to the cited approach.                                                                                  |
| The five listed aims are achieved                                                          | Some are demonstrated; others are design intentions or assertions. See the abstract findings above.                                                               | Important. Give each aim a corresponding demonstration or test, especially data-to-figure regeneration, positional information, and source-database immutability. |
| Section 4 shows oracle bone glyphs for 日 月 明 虫 工 虹 alongside sound and meaning             | The figures are present, but their presence does not validate the glyph identification or imply that the displayed decompositions are historical etymologies.     | Important. Explicitly separate modern decomposition from historical glyph evidence in the section introduction and figure captions.                               |

### 1.3 Three phrases that need special treatment

- “Consistently” — The examples show a consistent layout. They do not establish consistency across arbitrary inputs, fonts, languages, missing fields, or platforms. Retain the claim for the demonstrated output and add broader tests before generalizing.
- “Not manual work” — This confuses automated typesetting with automated linguistic analysis. The renderer removes repeated layout work; it does not eliminate the work of curating decompositions, pronunciations, meanings, or historical images.
- “A function of the data” — This is the most valuable architectural claim, but the wording is mathematically stronger than the evidence. Output also depends on styles, font selection, rendering settings, picture sets, and software versions. Prefer “generated reproducibly from structured character data and explicit rendering settings.”

Recommended abstract direction: State the actual contribution first: a Python-to-XeLaTeX pipeline that generates several character-decomposition views from structured records, with an optional aligned picture view. Then state the implementation and demonstrated examples. Keep the limitations explicit and avoid implying that the tool validates historical interpretations.

## 2. Oracle bone script, pictographs, and the six glyphs

Overall severity: Important. The paper's disclaimer about etymology is appropriate, but the prose immediately before it still encourages readers to interpret the pictures historically. The key distinction is between showing a glyph alongside a modern character and asserting that the glyph explains the modern character's origin or component structure.

### 2.1 Findings ranked by severity

[Important] “Chinese characters originated as pictographs.”

- Location: Section 1, p. 1, lines 25–29; repeated in the abstract, p. 1, line 9.
- Problem: The wording suggests a single origin for Chinese characters as a whole. Chinese writing includes pictographic, indicative, associative, and phonetic-semantic formations, among other historical categories.
- Fix: Write “Pictographic forms are an important part of early Chinese writing, including oracle bone inscriptions.” Keep the claim about modern characters separate from the discussion of ancient writing.

[Important] “the sun is a circle, the moon a crescent” and “a creature or a tool is drawn as what it is.”

- Location: Section 1, p. 1, lines 25–29.
- Problem: These statements present visual resemblance as settled interpretation. They do not identify the exact ancient glyph variants or their source records.
- Fix: Describe the specific images used in the figures, cite their source identifiers, and avoid treating resemblance as proof of original meaning.

[Important] “Reading 日 + 月 = 明 as sun and moon making bright, and 虫 + 工 = 虹 in the same way, gives:”

- Location: Section 4.1, p. 4, line 191.
- Problem: This sentence explicitly supplies a semantic explanation for two character constructions. A reader can reasonably interpret it as a historical or etymological claim, even though the paper later disclaims etymological intent.
- Fix: Replace it with a neutral introduction: “The following equations illustrate the modern component decompositions and their associated glosses; they are not proposed etymologies.”

[Important] “In the glyphs chosen here, 明 is a crescent next to a small box and not a sun and a moon, and 虹 is an arch with a head at each end.”

- Location: Section 4.1, p. 5, lines 250–257.
- Problem: This is better than asserting that the glyphs prove an etymology, but it still gives visual interpretations without documenting which dataset entries were selected or whether the proposed shapes and referents are accepted by paleographers.
- Fix: Use neutral visual descriptions and give the exact image IDs. If an interpretation is included, label it as tentative and cite a specialist source.

[Minor] “Modern characters have kept the sound and the meaning but lost most of the picture.”

- Location: Section 1, p. 1, lines 27–29.
- Problem: This oversimplifies historical change in both form and pronunciation. Modern characters do not uniformly preserve a single pronunciation or meaning.
- Fix: Replace with “Many modern character forms differ substantially from their earlier graphic forms.”

### 2.2 Character-by-character review

[Kanji of Sun or Day (日) | EJable](https://images.openai.com/static-rsc-4/AhJxeo-8ZKobclu0brqWKIiLmoN3JqInPzGewlWQGmEtkji7sWh1knmBwvj1i4LKnhxwo8yWjjDN_pkbAyJP8IAxHa0_GGEbJ0u2y2qlg3thLFL1runLiUFOj2YIBq6H0PdWvRHdDcSD6Qt0S6ZPwLZYHifKxcfiyMxc4lN2n8Y?purpose=inline)

日 — sun

Location: Section 4.1, pp. 4–5.

The sun interpretation is conventional, but the specific description “a circle” should be tied to the actual selected glyph, not generalized to the script. An image can show a circular or enclosed form without proving that every historical variant has the same shape.

Fix: Cite the HUST-OBC sample identifier and describe the displayed form literally.

[南湖星空很燦爛 ～月亮篇](https://images.openai.com/static-rsc-4/memrg4yDryalCSGGxwJzOSyeyPSjmdd5h7nRR_Iq_WuWh6jqhFalpyFjRJK5zjK90R1kPjKqMhr4YJbvCb0-7l3WATFprEgCRFm8VYrXJrIKshpwu5lxigQNyzMdufinVKZCNo-rE1HcSvN2YbcbXcKLoS0-1KF89Y2xySZVq4w?purpose=inline)

月 — moon

The identification as moon is conventional, but “a crescent” is an interpretation of a particular graphic form, not a sufficient description of the character's entire paleographic history.

Fix: Identify the selected sample and avoid using its shape as evidence for the history of 明.

[甲骨文 中與「天」相關的字 - 考古資料數位典藏創新計畫](https://images.openai.com/static-rsc-4/PNj4Q4uXuynWOrhrAw4COLdnEfIO7ioXc0i0M_n34Ychhx_mi3pqVbbeRizb7TxkWzxbivl68VZt6LbMHIhibcHAt6H_CgqmT5AHP_fBMgkd0R95bdSd7ePGHBjZJXY5cb0gocne8deEF-YUSw3GrJ0b8sJTEdwxQaaGOxmmXZ4?purpose=inline)

明 — bright

Highest-risk example. The relationship between the modern components 日 and 月 and the historical forms of 明 should not be presented as settled merely because the modern decomposition can be read as “sun + moon.” The paper itself notes that the selected glyph looks like a crescent beside a small box.

Fix: State that the modern decomposition and the selected ancient glyph are distinct data records. Avoid implying that the selected glyph confirms or refutes a specific etymology.

[あつじ所長の漢字漫談１１　蟹になぜ《虫》があるのか | kanji café（漢字カフェ）](https://images.openai.com/static-rsc-4/vwqNGxhG1FnSEFOjY9wXCNGcmPSNdRCxp8jx2viJAGrdOYsKeoTmxI3boMrHiZ8RWpovOcLPTOjh5W-VQIQOvMzuZcdVnchkacidAVPPN758u8h3S0G-YJ5e4fI2brgrpimuMk-wcCdDw7fzwWsRTopoc0eux9Xqr3DWN9ssv5s?purpose=inline)

虫 — insect

The gloss “insect” is a modern lexical label, not necessarily a full interpretation of every ancient form or its historical referent.

Fix: Distinguish the modern gloss from the identification of the source glyph. Record the chosen sample's provenance.

[048 工　甲骨365](https://images.openai.com/static-rsc-4/aBnDF7Fb1dbMSfhdbX2b7up48e5matf1q7xz4LpNSk4lZdQ2gLKEKbttEGzDpob9mymljkquZ2kZRMyu9MmAlXOZ3Oqu6lI4sWLxm5c-XWLjTtiHa8GefhozdJn2WcoAWx-So-EFTZ8lGtKdxt4zy6pHTst6oZ7kWbEQF8y5dFg?purpose=inline)

工 — work

The modern gloss “work” should not be read as evidence that an ancient glyph directly depicted work, or that the modern component's semantic label explains the historical formation of 虹.

Fix: Treat the gloss as lexicon data and keep it separate from the historical glyph description.

[【蛸、蟹、虹】虫っぽくないのになんで“虫”編なの？【蛤、蛯、蚫】｜ku](https://images.openai.com/static-rsc-4/6K0QCXWRpANI3cjm6w__gibMfOufPIM-oxSEy4ZG1jC-MIXqw-vRQmb6PEXJU1U4zazXly0h6P4J72lxd5K616SGdjmlTkOGAMf5uEzsS7h8v88fqkCqYk_deJVcslkeUhk07TA571UzTqkSYPv0q46rMztsJgPV1skcduj-Reo?purpose=inline)

虹 — rainbow

The sentence about an arch with a head at each end is a visual interpretation, not a demonstrated paleographic conclusion. The modern decomposition 虫 + 工 and the English gloss “rainbow” do not establish the origin of the ancient form.

Fix: Describe the visible features without identifying them as specific creatures or anatomical parts unless supported by a specialist source.

The images above are illustrative visual references, not verified reproductions of the six exact HUST-OBC samples used in the paper. I have not matched them to the paper's PNG files.

### 2.3 Does the paper maintain its “no etymology” disclaimer?

Not consistently enough. Section 5, p. 6, lines 275–276 says, “We make no claim about the etymology of any character: the figures show the data.” That is a sensible disclaimer, but the sentence on p. 4, line 191 about “sun and moon making bright” and the introductory claims on p. 1 invite historical interpretations.

The disclaimer also cannot neutralize misleading surrounding prose. A reader encounters the interpretive narrative before the disclaimer.

Concrete fix: Move a short statement of scope to the beginning of Section 4.1:

> The figures juxtapose modern character decompositions, dictionary glosses, and selected oracle bone glyph images. These records serve different purposes; their juxtaposition does not establish a historical relationship between the modern components and the ancient forms.

Also add the source identifier and attribution to each ancient glyph, preferably in a table or figure note.

## 3. Related work

Overall severity: Important. Section 5, p. 6, lines 261–266 correctly acknowledges that the paper did not survey other tools. That admission is honest, but the resulting related-work section is too thin to establish what is distinctive about zitex.

The paper does not need to claim novelty over every existing tool. It does need to explain what each neighboring category already does and what zitex adds.

### 3.1 Missing tools and resources

[輸入文字 · \["vChewing 唯音"\]](https://images.openai.com/static-rsc-4/xJ-OrmffjpE0-74lPxSoY8jU-dS0jkVi_L4sDTOouoGQ0bYwcrlR40xCy6d4LkYqi6KA5kZJge-y9HRLPz97JK2ipcWzg3u2YPMzEM3F8EEZltzmrF4ObcBfeOECrMyny5SftAFtMABKSB4cNWAoH-5xC8IvHV2GXUE4xw5SNjg?purpose=inline)

1\. LaTeX pinyin and ruby annotation

- [CTAN: CJK](https://www.ctan.org/pkg/cjk)
- [Example of the ](https://github.com/thomastan/lytex/blob/master/source/sometex/basic-cjk/texmf-local/tex/latex/cjk/ruby.sty)[`ruby`](https://github.com/thomastan/lytex/blob/master/source/sometex/basic-cjk/texmf-local/tex/latex/cjk/ruby.sty)[ package](https://github.com/thomastan/lytex/blob/master/source/sometex/basic-cjk/texmf-local/tex/latex/cjk/ruby.sty)

The CJK package ecosystem supports Chinese text, pinyin-related typesetting, and ruby-style annotations.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.ctan.org\&sz=32)

CTAN

+1



What the paper should say: These tools already handle some of the pronunciation-annotation problem. Explain that zitex's contribution is not simply putting pinyin above characters, but generating multi-component equations and structured spatial diagrams from a common record. Check compatibility and overlapping capabilities rather than implying that annotation is generally manual.

[Your Phone Shows Stroke Order. Can It Teach the Character? | Hidden Dragon Blog](https://images.openai.com/static-rsc-4/TfDS7U4zPMpZmPQJVunzKR-RG4PaRnAGa53pLoAwqXQVa4FuPzuwlZUHc8vC8uCqYncDdjHTNseF9Ymg4OnpwJ0dsAbzBqI_QvqckiBfhykJE-q53if6n7-pcLByrpY6Uzx9jc83CnS-udd3xQfPtARsX3h6Xt3GcyqiNptfSFU?purpose=inline)

2\. Make Me a Hanzi and Hanzi Writer

- [Make Me a Hanzi](https://www.skishore.me/makemeahanzi/)
- [Hanzi Writer](https://github.com/chanind/hanzi-writer)

Make Me a Hanzi provides character dictionary and graphical data, including decomposition and stroke paths; Hanzi Writer uses related data for stroke-order animations and practice.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.skishore.me\&sz=32)

Free, open-source Chinese character data

+1



What the paper should say: These are adjacent resources, not direct replacements for the whole zitex workflow. Compare their decomposition or graphic data with zitex's position-coded representation, then explain whether the datasets can be imported or used as an alternative source.

[NeurIPS Poster IF-Font: Ideographic Description Sequence-Following Font Generation](https://images.openai.com/static-rsc-4/XvrAx81wAK-U2ojt-_uplxNtmchv7i9elzDk4nGT37srFxldqzlvGAyNfKWUwTEJQVQ57rp6DZ6oHRJIqJsW89PFeBAnRfDGJR4lv04B4ao5aqn3-WCo6mQN69dlkwwMtibvrx7_ZGT_EhV469iMHKWXmlTZmqfqdFAcrYSKnAw?purpose=inline)

3\. Ideographic Description Sequences (IDS)

- [cjkvi-ids](https://github.com/cjkvi/cjkvi-ids)
- [Unicode Standard, Section 18.2: Ideographic Description Characters](https://www.unicode.org/versions/latest/core-spec/chapter-18/)

The draft already cites cjkvi-ids and Unicode. It says IDS records do not give positions or figures, but that distinction needs to be made more carefully: IDS operators do encode structural relations such as left–right and top–bottom arrangements, even though a flat IDS string is not the same as zitex's eleven-position model.

What the paper should say: Compare representational capacity, not just string versus figure. Show one character encoded as IDS and as a Zi-Matrix, and explain which information is retained, added, or lost.

[中国最早的文字——甲骨文|占卜|殷墟|金文|卜辞|龟甲_新浪新闻](https://images.openai.com/static-rsc-4/xnRrgodef6pg_DNQEzKOp5xnk11cQi8GmYyouQ_HyqR81hdqytUW-4DAakaiBNxnX-dGYDQG6o5Pvse87_beODFbIgo4Qgd3AJ1ysxupQEnjCgsFUWt4jIhAPnb9k-UNwdoOZJBygxlSUjk8-rdcZ1h4437BRiN-OSYeNq3Qrww?purpose=inline)

4\. HUST-OBC and EVOBC

- [HUST-OBC repository](https://github.com/Pengjie-W/HUST-OBC)
- [Wang et al., “An open dataset for oracle bone character recognition and decipherment,” Scientific Data (2024)](https://doi.org/10.1038/s41597-024-03807-x)
- [Guan et al., “An open dataset for the evolution of oracle bone characters: EVOBC”](https://arxiv.org/abs/2401.12467)

HUST-OBC is a dataset for oracle bone character recognition and decipherment, assembled from multiple sources. EVOBC focuses on character forms across historical stages.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub

+2



What the paper should say: Cite the dataset paper, explain how individual samples were selected, and distinguish an image collection from an expert-validated historical explanation. Where the source provides provenance, preserve the original identifiers rather than only renaming files to Unicode code points.

[Is ‘Writing’ Much Older than We Suspected?](https://images.openai.com/static-rsc-4/C7UgL_GtdxgxchVnumhun2DXbCgBHXLKXT1Gs5UumgdTQrx4Pn4Vi3xh6GwqKSaWl6kvzIZa5bMQFmFiIwgQyz2uZa8RrJe0r_V2xL5GtZs-WazUndfmyIWelI8_wN0IiQ3xJzWbr0EEwBZZvJ935VUtEupq12Oe5Qft9BwwzoY?purpose=inline)

5\. Historical glyph and character-evolution resources

- [Chinese Etymology — Richard Sears](https://hanziyuan.net/)
- [GlyphWiki](https://glyphwiki.org/)

These are relevant resources for comparing historical forms or inspecting glyph variants. I have not verified the current coverage, provenance, or licensing of each specific entry for the six characters in this paper.

What the paper should say: Include them as neighboring resources, with a clear description of their scope and limitations. Do not imply that a site provides authoritative paleographic conclusions merely because it displays ancient-looking forms.

### 3.2 What is the actual research gap?

The most defensible gap is not “no tool automates Chinese character diagrams.” The existing ecosystem is too broad for that claim without a systematic survey.

A narrower, testable claim would be:

> zitex combines a position-coded character representation, language-dependent glosses and readings, multiple generated LaTeX views, and optional per-component picture sets in a single data-driven workflow.

The paper should then demonstrate that this combination is useful. A compact comparison table would be sufficient:

| Capability                          | Existing resources                                   | zitex's stated contribution                                                |
| ----------------------------------- | ---------------------------------------------------- | -------------------------------------------------------------------------- |
| Pinyin/ruby annotations             | CJK and related LaTeX tools                          | Integrates pronunciation into component-level equations                    |
| Character decomposition data        | cjkvi-ids, Make Me a Hanzi                           | Adds an eleven-position representation and custom patterns                 |
| Stroke order and character graphics | Hanzi Writer, Make Me a Hanzi                        | Focuses on static decomposition figures rather than animation              |
| Historical glyph images             | HUST-OBC, historical glyph resources                 | Selectable image sets aligned with modern components                       |
| Multiple generated views            | Must be compared with existing diagramming workflows | One record can generate formula, equation, matrix, tree, and picture views |

This would acknowledge overlap without diminishing the actual engineering contribution.

## 4. Design decisions

Overall verdict: The core architecture is sensible. The single-grid picture view, opt-in `pictmath` style, named picture sets, and build-time emoji rasterization are reasonable decisions for a XeLaTeX-focused tool. They reduce coupling between the data model and presentation. The remaining concerns are interface compatibility, fallback behavior, and portability—not reasons to abandon the design.

The discussion below assesses the decisions described in the paper and the design details supplied in your prompt. It is not a source-code-verified finding about every implementation detail.

### 4.1 One `array` grid instead of stacked `\underbrace` labels

[Minor] Keep the grid.

- Location: Section 3, p. 3, lines 106–116; Section 4.1, pp. 4–5.
- What works: One grid allows all component labels and images to share consistent rows. A picture row remains visually aligned even when individual components lack pictures. This is easier to understand than deeply nested labels.
- What could break: Long glosses can make a column disproportionately wide; many components create a very wide equation; differing image dimensions can affect perceived alignment; missing cells can look like missing data rather than intentional absence.
- Fix: Keep the grid but document its sizing rules. Add examples for missing pictures, long glosses, mixed CJK/Latin text, and a character with many components. Consider an optional compact or wrapped layout for prose-oriented documents.

The main limitation is horizontal layout, not the use of an array itself. The paper already acknowledges overflow; the next step is to make the failure mode predictable.

### 4.2 A separate opt-in `pictmath` style

[Minor] Good separation of concerns.

- Location: Section 3, p. 3, lines 106–116.
- What works: Documents that do not need pictures should not incur image lookup, rasterization, or image dependencies. The ordinary equation view can remain lightweight.
- What could break: Users may assume that the picture style works wherever the normal equation style works. A macro that works in a MathJax rendering context may fail if the selected style needs external files or engine-specific commands.
- Fix: Make unsupported combinations explicit. Provide a short compatibility table for `math`, `matrix`, `tree`, and `pictmath`, including XeLaTeX, other TeX engines, MathJax, and KaTeX.

The paper already says that the picture view is unavailable in MathJax. Keep that statement prominent in the usage documentation rather than treating it as a minor implementation footnote.

### 4.3 Named picture sets selected per character

[Minor] A strong data-model decision, provided the selection rules are explicit.

- Location: Section 3, p. 3, lines 110–116; Section 4.1, pp. 4–5.
- What works: A document can switch between emoji, oracle bone glyphs, and other image collections without changing the decomposition itself. This makes comparisons and alternative presentation styles practical.
- What could break: Duplicate entries, ambiguous set precedence, absent images, or an image accidentally associated with the wrong character. A Unicode code point is not sufficient to identify a particular historical glyph variant.
- Fix: Define the lookup key and precedence rules, including what happens when the requested set exists but lacks a picture. Preserve the dataset's original glyph ID and source provenance in addition to the normalized filename.

For historical data, the distinction between which character and which glyph sample is essential.

### 4.4 Emoji rasterized to PNG at build time

[Minor] Reasonable for XeLaTeX, with reproducibility trade-offs.

- Location: Section 3, p. 3, lines 110–112.
- What works: Rasterization avoids relying on XeLaTeX to render color emoji directly. Prebuilt PNGs also reduce runtime complexity in the TeX document.
- What could break: Output may vary with installed emoji font versions, rasterizer behavior, image resolution, and platform defaults. A user may rebuild a figure and obtain a different emoji image even when the input YAML has not changed.
- Fix: Record the emoji font, rasterizer, and relevant versions; define a fixed output size and resolution; and preserve generated PNGs for release builds.

The build-time conversion should also fail loudly when an emoji cannot be rendered. Substituting a blank image without a clear diagnostic would undermine the paper's claim of predictable generation.

### 4.5 Compatibility and portability

| Environment        | Expected issue                                                                        | Recommended action                                                                       |
| ------------------ | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| XeLaTeX            | Intended target; depends on packages, fonts, and generated assets                     | Supply a clean build script and test from a fresh environment                            |
| pdfLaTeX           | Unicode CJK font handling and XeLaTeX-specific commands may fail                      | Declare it unsupported rather than implying general LaTeX compatibility                  |
| LuaLaTeX           | Font and CJK behavior may differ; support is not established                          | Test separately before claiming support                                                  |
| Overleaf           | Availability of packages, local font files, and generated images matters              | Provide a minimal example project and state the required compiler and files              |
| MathJax/KaTeX      | Image-based style is unavailable; macro definitions may not exist in the web renderer | Keep a documented equation-only fallback                                                 |
| Long equations     | Grid width can exceed text width                                                      | Add a compact option or a clear width warning                                            |
| Right-to-left text | Directionality, column order, mixed-script shaping, and image placement may differ    | Test an RTL language explicitly or document that the current language support is limited |

Bottom line: Preserve the architecture. The design should be presented as an intentionally scoped XeLaTeX solution, not a general cross-engine typesetting framework.

## 5. Reproducibility

Severity: Blocker for a reproducibility claim; important for the paper's arXiv readiness.

The PDF documents a Python-to-LaTeX workflow and includes commands for generating example figures. However, I could not execute the repository's scripts in this review: the uploaded artifact is the PDF, and my attempt to clone the public GitHub repository failed because the environment could not resolve GitHub. I therefore cannot honestly report a successful or failed execution of either requested script.

The publicly visible repository README identifies the project as a Python package requiring Python 3.10 or newer, XeLaTeX, TikZ, xeCJK, fontspec, amsmath, and a CJK font; it also says Inkscape is needed for SVG glyphs.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub



### 5.1 Required build checks

| Check                                   | Status in this review                                                                         | What would settle it                                                                          |
| --------------------------------------- | --------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `examples/pict/build.sh`                | Not executed                                                                                  | Run it from a clean checkout and retain the full stdout/stderr and exit status                |
| `./make-arxiv.sh` in `docs/paper/arxiv` | Not executed                                                                                  | Run it from a clean checkout with no pre-existing generated files                             |
| Figures in Section 4                    | Visually present in the uploaded PDF                                                          | Rebuild and compare the resulting figure assets and PDF                                       |
| Full database dependency                | The paper explicitly acknowledges that the full development database is not in the repository | Demonstrate that the released example build does not need it                                  |
| Python version                          | Not independently tested                                                                      | Declare the minimum supported version and test it in CI                                       |
| Font availability                       | Not independently tested                                                                      | Test both with the bundled subset and with a clean TeX installation                           |
| Inkscape                                | Repository README says it is needed for SVG glyphs                                            | Establish whether the arXiv examples actually invoke SVG conversion or use only prebuilt PNGs |

### 5.2 Hidden dependencies to document

[Important] Python packages and versions. Pillow is relevant to the stated emoji rasterization pipeline; other dependencies may be declared in the project configuration, but I have not inspected the exact dependency list in the current source checkout.

[Important] Font selection. The build may depend on a system-installed color emoji font to generate the images, even if the final paper bundles the generated PNGs. Noto Serif CJK SC is also identified as part of the arXiv source. The exact font files and versions must be recorded.

[Important] Generated artifacts. A script that succeeds only because PNGs, YAML files, snippets, or font configuration from a previous run are already present is not a reproducible build. The scripts should generate all required outputs from declared inputs or explicitly identify checked-in generated assets.

[Important] Database availability. The paper says the database used for development is not included in full. This is acceptable if the paper's examples use a self-contained subset. It is not acceptable if rebuilding the figures silently requires the missing database.

[Minor] TeX toolchain. The paper should list the relevant TeX Live packages and, ideally, a tested version or container image. A dependency list alone does not guarantee identical output across TeX installations.

### 5.3 Recommended reproducibility standard

The arXiv build should work from a clean checkout using a single documented command, with no network access and no reliance on the author's local configuration.

For example, the build should:

1. Check the Python version and required executables.
2. Generate or validate all required snippets and images.
3. Compile with XeLaTeX.
4. Fail on missing required files or unresolved references.
5. Report the final PDF path and return a nonzero status on failure.
6. Run in continuous integration and retain the build log.

The full development database does not need to be bundled if the paper's examples can be rebuilt independently from the released data.

## 6. Licensing and data

Overall verdict: The separation of code and third-party asset licenses is correct in principle. The notice is a good start, but I would not call the licensing fully verified without checking the exact source assets and the font license files.

The repository's public `NOTICE` explicitly states that the code is MIT-licensed, the oracle bone glyph images are CC BY-NC 4.0, the character data derives from CC-CEDICT under CC BY-SA 4.0, and the bundled Noto fonts are under the SIL Open Font License 1.1.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub



### 6.1 CC BY-NC glyph images in an MIT code repository

[Important] Acceptable as a mixed-license repository, but not as an unrestricted MIT release.

- Location: `NOTICE`, Sections 1 and 4; paper p. 6, lines 283–287.
- What is correct: A repository can contain MIT-licensed code alongside separately licensed images. The MIT license does not automatically relicense the images.
- What is risky: A repository-level badge or broad statement that “zitex is MIT-licensed” can lead readers to believe that all bundled content can be reused commercially.
- Fix: Keep the explicit asset-level license notice, add a prominent mixed-license warning to the README, and ensure each distributable archive includes the notice.

The noncommercial restriction also matters for downstream uses of the paper's figures. The images may be fine for qualifying noncommercial uses, but the license does not grant general commercial reuse. Whether a particular distribution or use is permitted depends on the applicable terms and circumstances; this is not a legal opinion.

### 6.2 CC BY-SA 4.0 glosses derived from CC-CEDICT

[Important] Verify the complete attribution and share-alike chain.

- Location: Paper p. 6, lines 283–287; repository `NOTICE`, Section 2.
- What is correct: The paper acknowledges CC-CEDICT as the source of the English glosses.
- What remains uncertain: Whether all copied or adapted dictionary material is properly attributed in each distributed form, and whether all derived datasets are handled consistently under the applicable license.
- Fix: Include the exact source/version, attribution, license URL, and a description of modifications in the data package. Preserve this information when generating YAML files and PDFs.

The source attribution should be machine-readable where practical, not merely present in a repository document that may be separated from the data.

### 6.3 Bundling a Noto Serif CJK SC font subset in an arXiv source

[Important] Generally compatible with the OFL, subject to compliance with the exact font license and font naming rules.

- Location: `docs/paper/arxiv/fonts/`; paper Section 3, p. 3, lines 126–128.
- What is correct: The SIL OFL permits redistribution and modification of covered fonts under its conditions, including appropriately licensed subsets.
- What to verify: The exact subset's provenance, inclusion of the license text, naming restrictions, and whether the font was modified only by subsetting. The notice says the font was subset without adding glyphs, which is useful but should be verified against the actual artifact.
- Fix: Include the applicable OFL text and a provenance record alongside the subset. Check the reserved font names and other conditions against the actual font's license metadata.

arXiv source submission is not inherently incompatible with bundling a properly licensed font. The relevant question is whether the submitted archive and subsequent redistribution comply with the font's license.

### 6.4 Missing licensing checks

[Minor] Emoji images and source provenance.

The `NOTICE` says the non-oracle-bone emoji pictures are generated from Google's Noto Color Emoji font.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub

&#x20;The release should establish which font version produced the checked-in images and preserve the license notice even when the font itself is not bundled.



[Important] Glyph image provenance.

The notice describes renamed, converted HUST-OBC images. Verify that each image's source record is traceable, that the dataset's actual terms cover the intended reuse, and that no additional restrictions arise from underlying source publications.

[Conclusion]: The mixed-license model is sound. The remaining work is to make the licensing chain auditable, ensure attribution survives generated exports, and avoid presenting the entire repository as if every asset were MIT-licensed.

## 7. Code quality

Overall severity: Important, with source-level verification outstanding.

The requested source files were not available for direct inspection in this review. I will not invent line-specific Python bugs or claim that a function has a defect without reading its implementation. The findings below distinguish discrepancies visible in the paper from concrete tests and source checks needed before publication.

### 7.1 Python and LaTeX interface

[Important] Verify that the filename contract is identical on both sides.

- Location: Section 3, p. 2, lines 80–85; `src/zitex/render.py`; `src/zitex/build.py`; `zitex.sty`.
- What is wrong or unproven: The paper documents a snippet naming convention, but the source-to-LaTeX contract has not been independently verified. The example filename `u660e-pictmath-obs-zh.tex` raises a specific question: does the generator encode the style, picture set, and language in precisely the same way that the LaTeX package constructs the requested filename?
- Fix: Define one canonical filename function and use it, or generate a manifest that the LaTeX side reads. Add integration tests for `math`, `pictmath`, named picture sets, language variants, and alternate readings.

The most valuable test here is not another unit test of filename formatting. It is an end-to-end test that generates a snippet and proves that the corresponding LaTeX macro includes that exact file.

### 7.2 Lexicon and picture resolution

[Important] Missing and malformed entries need explicit diagnostics.

- Location: `src/zitex/lexicon.py`; `src/zitex/render.py`, `render_pictmath`.
- What to check: Unknown picture-set names, missing image files, unsupported emoji, invalid language keys, empty glosses, malformed pinyin, and conflicting lexicon entries.
- Failure mode: A renderer can produce a plausible but incomplete equation if an invalid entry silently becomes an empty cell. That is especially dangerous when an empty cell might be mistaken for a deliberate absence of a glyph.
- Fix: Distinguish a deliberately absent value from a failed lookup. Emit structured warnings with the character, component, field, and selected picture set. Provide a strict mode that makes unresolved required assets fatal.

### 7.3 Build and rasterization

[Important] The build should be deterministic and fail loudly.

- Location: `src/zitex/build.py`; `examples/pict/build.sh`; `docs/paper/arxiv/make-arxiv.sh`.
- What to check: Whether failed rasterization, missing fonts, subprocess failures, or missing source files propagate a nonzero exit status; whether existing outputs can conceal failures; whether PNG dimensions and resolution are stable.
- Fix: Check subprocess return codes, validate required output files, and fail the build if a required image cannot be generated. Use temporary output directories and replace final artifacts only after a successful build.

### 7.4 Validation semantics

[Important] Warnings must not be confused with successful validation.

- Location: Section 3, p. 3, lines 122–124; `src/zitex/lexicon.py`; `src/zitex/build.py`.
- What is wrong or unproven: The paper says that unknown positions, invalid patterns, overlapping regions, and misplaced radicals are warnings rather than errors because the data is under review. That is defensible for exploratory work, but the reader needs to know whether the build itself can distinguish a successful validation from a build that merely completed with warnings.
- Fix: Separate `validate`, `render`, and `strict build` outcomes. Record warning counts and return a nonzero status when strict validation detects a violation. Preserve a permissive mode for research exploration.

### 7.5 Tests

[Important] The reported tests do not establish end-to-end reproducibility.

- Location: Repository `tests/test_pipeline.py`, `tests/test_ui.py`; paper Section 3, p. 3.
- What is wrong or unproven: Even if unit tests pass, they do not establish that the picture view, font fallback, filename lookup, rasterization, and XeLaTeX compilation work together.
- Fix: Add integration tests for:
  - A component with no image.
  - A requested picture set with no matching image.
  - An unsupported emoji or unavailable emoji font.
  - A missing CJK glyph and font fallback.
  - Different languages and alternate readings.
  - A generated filename that must be consumed by `zitex.sty`.
  - A clean build with no pre-existing generated artifacts.
  - A failed build that returns a nonzero status.

The six known test failures on the author's machine should not be reported as newly discovered defects in this review. They do, however, reinforce the need for a clean, documented test run before submission.

### 7.6 Additional checks for the requested files

| File                                      | Specific review target                                                                                                            |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `src/zitex/lexicon.py`                    | Schema validation, duplicate keys, fallback precedence, empty values, and provenance preservation                                 |
| `src/zitex/render.py` — `render_pictmath` | Grid dimensions, column alignment, empty cells, escaping, math-mode safety, long labels, image sizing, and missing-image behavior |
| `src/zitex/build.py`                      | Dependency checks, subprocess errors, deterministic output, stale artifacts, path handling, and cleanup                           |
| `zitex.sty`                               | Macro option parsing, filename construction, missing-file handling, warnings, and consistency with the Python naming scheme       |

What I would prioritize: the generator–package filename contract and silent failure handling. These directly affect whether the published architecture behaves as described.

## 8. Writing and presentation

Overall severity: Important. The paper is readable and relatively short, but it spends too much of its limited space defending a broad motivation and too little demonstrating the precise engineering contribution.

### 8.1 Findings ranked by severity

[Important] The historical motivation overstates what the tool establishes.

- Location: Abstract and Section 1, pp. 1–2.
- Problem: The paper moves from pictographic origins to modern decompositions and then to ancient glyph images in a way that invites an etymological reading. This is inconsistent with the later disclaimer.
- Fix: Introduce the distinction between modern structural decomposition and historical glyph evidence before the examples, not after them.

[Important] The contribution is not evaluated against a baseline.

- Location: Sections 3–5, pp. 2–6.
- Problem: The paper demonstrates that the tool generates figures, but does not measure whether it reduces effort, improves consistency, or catches errors compared with manual construction or existing tooling.
- Fix: Add a small reproducible case study: edit one character record, regenerate several views, and show that all views update consistently. A brief comparison with manual figure editing would help establish practical value without requiring a large user study.

[Minor] The notation discussion is denser than the implementation evidence.

- Location: Section 2, p. 2, lines 56–75.
- Problem: The eleven positions, Unicode IDS operators, extra operators, and radical rule receive substantial space, but the relationship between notation and generated output remains difficult to evaluate from the text alone.
- Fix: Keep one compact table of position codes and add a single worked example showing the input representation, the generated view, and what information the view preserves.

[Minor] Section 3 repeats capabilities without a clear hierarchy.

- Location: Section 3, pp. 2–3.
- Problem: Views, pictures, readings, validation, fonts, and data are presented as parallel topics, although they differ in importance to the paper's central contribution.
- Fix: Organize them as (1) data model and pipeline, (2) rendering views, and (3) practical constraints. Move lower-level font and fallback details into a short implementation note if space is tight.

[Minor] The limitations section combines unrelated kinds of uncertainty.

- Location: Section 5, p. 6, lines 267–276.
- Problem: Engine compatibility, layout overflow, glyph coverage, database conversion failures, and uncurated glosses are listed together without distinguishing technical limitations from data-quality limitations.
- Fix: Separate “Implementation limitations” from “Data and historical interpretation limitations.”

### 8.2 The three sentences I would cut first

These are the first sentences I would remove or replace to improve precision and free space for reproducibility details.

CUT 1 · Section 1, p. 1, lines 25–29

> Chinese characters originated as pictographs. The oracle bone script, carved on turtle shells and animal bones in the late Shang dynasty more than three thousand years ago, still shows the pictures: the sun is a circle, the moon a crescent, and a creature or a tool is drawn as what it is.

Why: It is an overgeneralized historical opening and makes the paper's technical contribution harder to distinguish from an argument about the origins of writing.

CUT 2 · Section 1, p. 1, lines 33–37

> Today this is manual work. Pinyin and glosses are placed above and below the characters by hand, pictures are pasted and aligned one by one, and the decomposition is drawn in a graphics program or in TikZ.

Why: The universal claim is unsupported. Replace it with a shorter, qualified statement about the manual layout steps that zitex automates.

CUT 3 · Section 4.1, p. 4, line 191

> Reading 日 + 月 = 明 as sun and moon making bright, and 虫 + 工 = 虹 in the same way, gives:

Why: It creates an etymological implication that the paper later disclaims. Replace it with a neutral description of the modern decompositions and glosses.

### 8.3 The one question a skeptical reader will ask

“What can zitex demonstrate that I could not already achieve with existing character data, a LaTeX annotation package, and TikZ—and what evidence shows that the combined workflow is more useful or reliable?”

The current paper establishes that the implementation exists and produces several views. It does not yet demonstrate the size of the advantage or the boundaries of its unique contribution.

A compact experiment would answer much of this question: choose a small set of representative characters, update their source records, regenerate every view, and compare the resulting workflow with manual figure editing and one relevant existing tool. Report failures and limitations as well as successful outputs.

## 9. arXiv readiness

Verdict: Not yet ready for submission in its present form. The paper is short enough for a practical software note, and the repository describes a plausible build architecture, but the historical wording, unverified source-to-LaTeX interface, and lack of a confirmed clean build are material issues.

### 9.1 XeLaTeX and `00README.json`

[Blocker until verified] The actual arXiv source archive must compile independently.

- Location: `docs/paper/arxiv/00README.json`, `docs/paper/arxiv/make-arxiv.sh`, bundled fonts and image assets.
- What could fail:
  - A required `.tex` snippet or PNG is absent from the submitted archive.
  - The README selects XeLaTeX but the build script or included files assume a different engine.
  - A font path works locally but is not preserved or referenced correctly in the archive.
  - A system font is assumed to exist but is not installed on the arXiv build system.
  - A script uses a Python dependency or executable unavailable in the build environment.
  - Stale generated files conceal a missing build step.
- Fix: Generate the submission archive from a clean checkout, inspect its complete file list, and compile it in a clean environment using the exact engine selected by `00README.json`.

The paper's bundled Noto Serif CJK SC subset can improve portability, provided the actual TeX configuration points to that file and all necessary license terms are included. Bundling the font alone does not guarantee that the font will be found.

### 9.2 Rendering differences

[Important] Local PDF appearance may differ from arXiv output.

- Fonts: A fallback font may differ between machines, affecting glyph appearance and line widths.
- Emoji: Build-time rasterization is sensitive to the font and rasterizer used.
- Image inclusion: PNG dimensions and bounding boxes may influence row alignment and overall equation width.
- TeX packages: Different package versions can alter spacing, macro behavior, or font loading.
- Page layout: Slight width differences can change line breaks or cause a wide picture equation to extend beyond the page.

Fix: Bundle the exact assets used for the final paper, record the build environment, and compare the clean-build PDF with the submitted PDF. Do not rely on rebuilding the figures during arXiv processing if the final source can include the generated artifacts.

### 9.3 Subject classification

My recommendation is cs.CL (Computation and Language) if the paper is positioned as a tool for computational representation and analysis of Chinese characters. It is a more natural fit than cs.DL, whose focus is digital libraries, or cs.HC, which would be more compelling if the main contribution were a studied human-computer interaction design.

However, the current paper is primarily a typesetting-tool description. It does not yet establish a computational-linguistics result or evaluate the tool for a linguistic task.

Recommended choice: Use cs.CL as the primary category if the framing emphasizes character representation and computational linguistics, with a secondary category only if justified by the final contribution. If the authors retain a purely software-engineering framing, they should reconsider whether a computer-science category is the best primary home rather than assuming that the subject matter alone determines the classification.

### 9.4 Submission checklist

Before submission, I would require these items:

- Revise the abstract and introduction to distinguish automation from data curation.
- Remove or qualify historical claims about the six glyphs.
- Add a short related-work comparison with specific existing tools.
- Resolve and test the Python/LaTeX snippet naming contract.
- Run both requested build scripts from a clean checkout.
- Verify that the full arXiv archive contains every required font, image, snippet, and license notice.
- Compile using the engine selected by `00README.json`.
- Confirm that the resulting PDF matches the intended final figures and page layout.
- State exactly what is included in the released examples and what depends on the unavailable full database.

## Not verified

The following items remain unresolved. They should not be interpreted as confirmed defects.

1\. Build execution: I could not run `examples/pict/build.sh` or `docs/paper/arxiv/make-arxiv.sh`. A clean checkout, dependency inventory, and complete build logs with exit statuses would settle whether the figures and paper rebuild successfully.

2\. Source-code correctness: I could not inspect the complete contents of `src/zitex/lexicon.py`, `src/zitex/render.py`, `src/zitex/build.py`, or `zitex.sty`. The filename-contract, silent-failure, and validation concerns in Section 7 are targeted review requirements, not confirmed implementation bugs. A source archive or direct access to those files would permit line-specific findings.

3\. Exact glyph provenance: I did not match the six images shown in the paper to their original HUST-OBC samples or verify their interpretations against specialist paleographic references. The actual PNGs, original dataset IDs, and expert references are needed.

4\. License compliance: I reviewed the repository's public `NOTICE` as displayed online, but did not inspect every distributed asset, the actual font subset, or the full applicable license texts. A file-by-file provenance and license audit would settle this.

5\. Compatibility: I did not test Overleaf, MathJax, KaTeX, LuaLaTeX, pdfLaTeX, or right-to-left rendering. The paper's XeLaTeX and MathJax limitations are taken from the supplied draft, not from independent execution.

6\. Historical interpretations: I did not establish a specialist consensus on the precise paleographic interpretations of 日, 月, 明, 虫, 工, and 虹. The paper should avoid strong historical claims until these are checked against appropriate specialist sources.

7\. arXiv compilation: I did not compile the complete source archive using the engine selected by `00README.json`. A successful local PDF is not sufficient evidence that the submitted archive will compile identically.

Final recommendation: Revise the historical framing and unsupported automation claims first, then perform a clean, reproducible build and verify the Python-to-LaTeX interface. Those changes would make the paper a more credible and appropriately scoped software contribution without requiring a major redesign of zitex.