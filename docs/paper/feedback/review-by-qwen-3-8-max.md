### Verdict
The work contributes a novel, data-driven LaTeX extension (`zitex`) that elegantly solves the manual typesetting of Chinese character decomposition by aligning sound, shape, and meaning into a unified, reproducible grid. It is ready for arXiv, as the code, documentation, and reproducible build scripts are robust, though the paper's introduction would benefit from tightening its claims and clarifying its relationship to etymological tools. The single most important fix is to explicitly address in the text how the tool handles the frequent etymological mismatch between modern structural decomposition and historical oracle bone glyphs, clarifying that this dual presentation is a deliberate feature for linguistic analysis, not an oversight.

### Findings

**1. Claims against evidence**
*   **Important:** "Presenting the three together and consistently is manual work today... and none of it is tied to the data behind it." — The tool demonstrates the solution, but the claim that *none* of this work is tied to data is an over-claim. Tools like `xpinyin` (which auto-generates pinyin from data) already exist for the sound dimension; `zitex`'s novelty is the *integration* of shape and meaning into the same aligned grid.
*   **Minor:** "A character is a short entry giving its decomposition and the position of each part in the eleven-position Zi-Matrix notation." — Demonstrated clearly in the examples and YAML structure.
*   **Minor:** "A further view adds a row of pictures under the meanings... in rows that line up." — Demonstrated successfully by the `pictmath` renderer.
*   **Minor:** "We describe... the limits of the present version." — Demonstrated; the paper honestly lists MathJax incompatibility and overflow issues.

**2. Oracle bone script statements**
*   **Important:** "In the glyphs chosen here, 明 is a crescent next to a small box... and 虹 is an arch with a head at each end. The figures show the data: a modern decomposition and an ancient glyph are separate records, and the picture row puts them side by side without interpreting either." — This is an excellent design choice. A paleography specialist would appreciate that the paper avoids claiming the modern decomposition (e.g., 虹 = 虫 + 工) is historically derived from the oracle bone glyph.
*   **Minor:** "Chinese characters originated as pictographs... the sun is a circle, the moon a crescent..." — A specialist might note that many early characters were phono-semantic or abstract, not purely pictographic, and that oracle bone script was already highly stylized. However, this is acceptable as a broad typographic generalization for a software paper.

**3. Related work**
*   **Blocker:** The statement "We did not survey other tools for drawing character decompositions, and a comparison is future work" is too weak for an arXiv paper. You must contrast `zitex` with at least two existing categories to establish novelty:
    *   **Pinyin/Ruby tools:** Mention `xpinyin` (CTAN) or `xeCJK` ruby features. Note that they handle the "sound" overlay but lack structural decomposition or meaning alignment.
    *   **IDS/Decomposition databases:** Mention CHISE (IDS) or HanziCraft. Note that while these projects map the decomposition data, `zitex` focuses on the *typesetting mechanics* (aligned grids, equation formatting) which these databases do not provide.

**4. Design**
*   **Important:** **One `array` grid vs stacked `\underbrace`.** This is an excellent decision. `\underbrace` cannot align vertically across multiple terms in an equation. The `array` guarantees that pictures and meanings share horizontal baselines across the entire reaction.
*   **Important:** **Separate opt-in style (`pictmath`).** Good decision. It keeps the default `math` view lightweight and compatible with MathJax/KaTeX, while `pictmath` correctly isolates the dependency on `graphicx` and XeLaTeX.
*   **Minor:** **What would break:**
    *   *Long equations:* The `array` grid does not support automatic line-breaking or scaling. A long equation with wide meanings will overflow the page. The paper acknowledges this, but users might expect `\resizebox` to be an option.
    *   *Overleaf/MathJax:* Handled correctly. MathJax users get the text-only `math` style; Overleaf users just need to select the XeLaTeX compiler.

**5. Reproducibility**
*   **Blocker:** **Pillow (PIL) and Emoji Fonts.** The build scripts (`build.sh`) do not explicitly check for or install Python dependencies like Pillow, which are required to rasterize emoji. If a user clones the repo and runs `build.sh` without Pillow installed, emoji pictures will silently fall back to empty cells. The README should list `Pillow` as a requirement for the `pict` view.
*   **Minor:** **Hidden dependencies:** Inkscape is required only if SVG glyphs are used. The bundled font subset in `docs/paper/arxiv/fonts/` is an excellent safeguard for reproducibility across different TeXLive versions.

**6. Licensing and data**
*   **Important:** **CC BY-NC in an MIT repo.** The `NOTICE` file correctly and sufficiently separates the MIT code from the CC BY-NC HUST-OBC images. This is legally acceptable as long as the restriction applies only to the assets, not the code itself.
*   **Minor:** **CC BY-SA glosses:** The glosses derive from CC-CEDICT. The `NOTICE` attributes this correctly. Users should be aware that generated YAML files containing these glosses inherit the CC BY-SA license.

**7. Code quality**
*   **Important:** **Snippet naming agreement:** `build.py: snippet_name` and `zitex.sty: \zitex@name` perfectly agree on the format `u<hex>-<style>[-<lang>][@reading]`. `scan_tex` correctly parses `pict=obs` into `pictmath-obs`. The synchronization between the Python builder and the LaTeX loader is robust.
*   **Minor:** **Silent failure in `emoji_to_png`:** If Pillow or the emoji font is missing, `lexicon.py` returns `False` and the picture is omitted without a warning. A `logging.warning` would help users debug missing pictures.
*   **Minor:** **`render_pictmath` column alignment:** The `array` uses `@{\hspace{3pt}}c` for all columns. Operators like `+` or `=` are centered in their cells, which may look slightly misaligned vertically compared to standard math operators, but this is acceptable for a grid layout.

**8. Writing**
*   **Important:** **Sceptical reader's question:** "How does `zitex` handle characters where the modern structural decomposition (e.g. 虹 = 虫 + 工) completely contradicts the etymological origin or the shape of the oracle bone glyph?" The paper implies the answer ("the figures show the data... without interpreting either"), but should explicitly state that this dual presentation is a feature for linguistic analysis, not an etymological claim.
*   **Minor:** **Three sentences to cut:**
    1. *"Modern characters have kept the sound and the meaning but lost most of the picture, which is why teachers and researchers keep placing the ancient glyph next to the modern character."* (Speculative and unnecessary).
    2. *"A Chinese character can be read as the product of a reaction in which its parts go in and the character comes out..."* (The chemical analogy is cute but distracts from the typesetting mechanics).
    3. *"The result is slow to produce, differs from one figure to the next, and must be redone when the underlying analysis changes."* (Over-complaining about the status quo).

**9. arXiv readiness**
*   **Important:** **arXiv build environment:** The `00README.json` correctly selects `xelatex`. The bundled font subset mitigates font availability issues on arXiv's older TeXLive environment. The `make-arxiv.sh` script testing the packed source in a clean directory is an excellent safeguard against build failures.
*   **Minor:** **Subject class:** `cs.CL` (Computation and Language) or `cs.DL` (Digital Libraries). `cs.CL` is appropriate for tools processing Chinese character data, while `cs.DL` fits the document preparation and scholarly typesetting aspect.

### Not verified
*   **Pillow/Emoji Font behavior on arXiv build server:** arXiv's build environment likely does not have Pillow or a color emoji font installed. Since the paper figures use oracle bone glyphs (PNGs) and emoji, the emoji figures might render as empty cells on the final arXiv PDF unless the author generated the emoji PNGs locally and committed them to the `zitex-out/picts/` folder before packing the source. *To settle:* Check if `zitex-out/picts/*.png` (without `-obs`) are committed to the `docs/paper/arxiv` folder in the tarball.
*   **Real-world database size:** The prompt notes the full decomposition database (6,200 characters) is not in the repository. *To settle:* Test the tool's performance and compilation time when loading and rendering the full 6,200-character SQLite database, rather than the 29-character sample YAML.