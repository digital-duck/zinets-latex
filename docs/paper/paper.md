---
title: 'zitex: typesetting Chinese character decompositions in LaTeX'
tags:
  - LaTeX
  - XeLaTeX
  - Chinese characters
  - Python
  - computational linguistics
  - visualization
authors:
  - name: Wen G. Gong
    orcid: 0000-0000-0000-0000   # TODO(author): your ORCID
    affiliation: 1
affiliations:
  - name: Digital Duck   # TODO(author): confirm the affiliation text
    index: 1
date: 2 October 2026   # TODO(author): the submission date
bibliography: paper.bib
---

<!-- TODO(author), before you submit to JOSS:
  - fill in the ORCID, affiliation and date above;
  - check "State of the field" against what you know: I wrote it from general knowledge and did not survey the tools;
  - check "AI usage disclosure" says what you did;
  - JOSS expects a public repository with an OSI licence (LICENSE is MIT), tests, documentation, and a visible
    development history; ask the editors how much history they want, the repository's first commit is 2026-09-30;
  - tag a release and archive it (for example on Zenodo) to get the DOI the review asks for. -->

# Summary

Chinese characters are built from smaller components, and *how* they are arranged (side by side, stacked,
enclosing, three across) carries information that a running text cannot show. `zitex` is a XeLaTeX
extension that typesets a character's decomposition as a one-line formula, a typeset equation with pinyin
and glosses (`日 + 寺 → 時`), a nested-box matrix, or a tree. The decompositions are kept as data (YAML or
SQLite), validated, and turned into LaTeX by a Python program. A thin package, `zitex.sty`, only includes the
generated files, so a paper contains commands such as `\zimath{時}` and never a decomposition.

# Statement of need

Researchers who write about Chinese characters (in linguistics, language teaching, computational
linguistics and the history of writing) draw decompositions by hand in TikZ or in a graphics program. The result is
tedious to produce, differs from figure to figure, and is detached from the data it illustrates. When the underlying
decompositions are revised, every figure has to be redrawn.

`zitex` makes the figure a function of the data. A character is a short entry with its shape, in prefix form
(`⿰日寺`), and the position of each part in the 11-position Zi-Matrix notation introduced in
[@gong2025] (`L R M U D Mi Mo LU LD RU RD`). A level's pattern, such as `L-M` or `LU-RU-M-LD-RD`, determines
the layout and, where Unicode has one, the matching ideographic description operator. The same data
gives four views, in several languages, and with named *readings*, which record competing
interpretations of the role of each part (semantic, phonetic) so that a paper can choose one.

# State of the field

The Unicode Standard defines ideographic description characters, and projects such as `cjkvi-ids`
[@cjkviids] distribute ideographic description sequences for tens of thousands of characters. These describe a
character as a string, and do not say where each part sits, nor do they produce a figure. `zitex` reads the
shape strings in this form and adds positions per level, because some arrangements (for example three parts in
a triangle, or a part that encloses another from two sides) have no single operator. For these `zitex`
adds a small set of operators and a general `<pattern>` form. Figures are made with TikZ [@tikz]
and Chinese text with `xeCJK` [@xecjk], which `zitex` builds on and does not replace. The English glosses
come from CC-CEDICT [@cedict], and are attributed in the data.

# Software design

Python does the parsing and the layout, and LaTeX does the typesetting (\autoref{fig:flow}). `zitex extract`
selects characters from a database and writes `chars.yaml`, `lexicon.yaml`, a `main.tex` and the snippets it needs.
Each snippet is self-contained (`u<hex>-<char>-<style>[-<lang>][@reading].tex`, the code point and then the character, with a `build_manifest.json` that lists them), and `zitex.sty` finds it by the
file name, so the package stays about 60 lines.

![The workflow. Python writes one snippet per character and style, and XeLaTeX includes them.\label{fig:flow}](flow.pdf){ width=100% }

Three choices matter for users. First, **validation** is built in: `zitex check` reports positions that overlap,
radicals placed in the centre, and patterns an operator does not allow, as warnings, since the source data is under
review. Second, **fonts** fall back in a fixed order (an override, the main font, fallback fonts, an image, a boxed
code point), so components without a Unicode code point can be set like any other. Third, the **data is not
touched**: a SQLite database is opened read only, `zitex` derives its own tables, and manual revisions are stored
with what they replaced so they can be reverted. A Streamlit application reviews and revises decompositions, and
generates a PDF for a list of characters. The package is tested with a suite of more than 300 tests, which compile
LaTeX when `xelatex` is available.

# Research impact statement

`zitex` is the typesetting component of the ZiNets project, which analyses the structure of more than 6,000
Chinese characters [@gong2025]. It is used to produce the decomposition figures and equations for
that work, and the demonstration paper that ships with the package (`zitex extract --annotation demo`)
is typeset with it. <!-- TODO(author): add anything real here: papers, courses or collaborators that use it. -->

# AI usage disclosure

The first design discussion was held with Google Gemini. Most of the code, the tests and the documentation were
written with Anthropic's Claude (Claude Code) under the author's direction. The author chose the notation and the
decomposition rules, made the data decisions recorded in the test data, and checked the generated figures.
<!-- TODO(author): edit this to say exactly what you reviewed. -->

# Acknowledgements

This work began as a conversation with Google Gemini, and the building, testing and writing phases were assisted by Claude Code of Anthropic. The character decompositions, solution design, and result validation are the author’s. The English glosses are derived from CC-CEDICT (CC BY-SA 4.0). <!-- TODO(author): funding, if any. -->

# References
