# Oracle Bone Script Dataset: Plan

Status: design notes for future work. Nothing in `src/zitex/` reads this directory yet, and there is no `zx_oracle` table. This is the author's next iteration after the SQLite bridge (M5): correlating oracle bone script with the decomposition data already in `db/zitex.sqlite3`, published here ahead of implementation so the plan can be reviewed first (same practice as `docs/DEV/claude/readme.md`'s milestone table).

## Goal

Build a dataset where each character (or undeciphered sign) carries three linked layers:

1. **Oracle script image(s)** — the earliest attested glyph form (rubbing or cleaned glyph), and where available the bronze / seal / kaiti stages after it.
2. **Decomposition for the semantic network** — the shape tree zitex already has (`zx_char` / `zx_part`: operator, positions, components) plus role (semantic, phonetic, force) and gloss.
3. **LVLM embedding** — a vision-language embedding of both the glyph image(s) and semantic network data, so shape similarity can be computed between signs, not just looked up by known structure.

**Ultimate goal**: use (1)+(2)+(3) together to help decipher currently undeciphered oracle bone signs, by finding glyph-similar and component-similar matches among already-deciphered characters.

## Why this is a natural next step

- `db/zitex.sqlite3` already holds the decomposition layer (layer 2) for 5,982 characters and 429 elemental characters (元字), built read-only from the author's working `zi.sqlite3` — see `docs/DEV/claude/db-integration.md`.
- The ongoing paper at `/home/papagame/projects/digital-duck/zinets/docs/arxiv/chinese-char-as-living-fossil` already assembled 1,328 glyph images (oracle, bronze, seal, kaiti) for 419 elemental characters, with an 84% paleographic attestation rate and 80 characters carrying a detailed case study. That image set (`figures/characters/{oracle,bronze,seal,kaiti}/`) is the natural seed for layer 1.
- What is missing is (a) oracle coverage for the non-elemental, composite characters in `zx_char`, (b) any coverage at all for *undeciphered* signs, and (c) the embedding layer.

## Source catalog (`oracle-bone-scripts.csv`)

This directory's CSV lists candidate sources, each tagged with whether it covers deciphered-only or deciphered + undeciphered material, and whether it includes images:

| Source | Deciphered / undeciphered | Images |
|---|---|---|
| HUST-OBC (GitHub) | both | yes |
| OBC306 | deciphered (labeled classes) | yes |
| Oracle-MNIST | deciphered (labeled classes) | yes, small MNIST-style |
| 小學堂 (Academia Sinica) | deciphered | yes |
| Chinese Etymology (hanziyuan) | deciphered | yes, evolution series |
| Wikimedia Commons | mostly deciphered | yes, mixed licenses |
| Wiktionary | deciphered | yes, uneven coverage |
| 殷契文淵 | both | yes, rubbings/photos |
| Academia Sinica IHP | both | yes, raw excavation rubbings |
| 《甲骨文合集》 (print) | both | yes, in print |
| 《甲骨文字詁林》 (print) | both, with decipherment discussion | yes, glyph tables |
| 《甲骨文字編》 (print) | both | yes, glyph tables |
| 《新甲骨文編》 (print) | mainly deciphered | yes, glyph tables |
| 人人认得甲骨文 (太和山居, WeChat) | deciphered | yes, per character |

Digital, image-bearing sources with undeciphered material (HUST-OBC, 殷契文淵, IHP) matter most for the decipherment goal, since the deciphered-only sources can only ever confirm layer 1 for characters already in `zx_char`.

**人人认得甲骨文** (local copy: `wechat-content.md`) is worth calling out separately: it is hand-crafted educational content — a personal WeChat series, not a bulk corpus or dataset — but unlike every other row above, each entry already pairs an oracle glyph image with a prose structural gloss (e.g. 家 = 宀 + 豕) and a catalog citation (合 / 马典 numbers). That is closer to what this project's layer 1 + layer 2 correlation actually needs than any bulk image dataset; it just doesn't scale past the ~900 characters the author chose to cover. Good for spot-checking `zx_char`/`zx_part` against an independent source, not for the undeciphered-sign side of the goal. Zinets being a research project, this kind of hand-curated secondary source is fine to lean on for validation, same caveats as any other web source: confirm reuse license before using content beyond personal review.

## Sketch of the data model

Extending the existing `zx_*` design (`db-integration.md` §2) with one more table, kept separate from the reviewed decomposition tables so speculative material never contaminates them:

| Table | Key | Holds |
|---|---|---|
| `zx_oracle` (new) | `zi` (nullable) or `sign_id` (for undeciphered signs, no code point) | `source`, `period` (oracle/bronze/seal/kaiti), `image_path_or_url`, `license_note`, `confidence` |
| `zx_embedding` (new) | `sign_id` or `zi` + `period` | `model`, `vector` (or a pointer to an external vector store), `inputs` (image-only, or image+semantic-network), `created_at` |

A deciphered character joins `zx_oracle`/`zx_embedding` to `zx_char`/`zx_part` on `zi`: its embedding is built from both the glyph image(s) **and** the decomposition/semantic-network data (operator, positions, components, roles, gloss), since both are known. An undeciphered sign has no `zx_char`/`zx_part` row, so its `zx_embedding` row is built from the glyph image alone. A proposed decipherment is a *hypothesis* (nearest neighbor of an undeciphered sign's image-only embedding against deciphered image+semantic embeddings, or shared components with a deciphered character), not written back into `zx_char` until confirmed.

## Related work (literature search, 2026-10-02)

Searched for prior work combining computer vision / LVLMs with structural or semantic reasoning for oracle bone decipherment, to check whether pairing a pre-existing, full-lexicon semantic/decomposition network (this project's 429 elemental roots + ~6,000-character decomposition trees, built with no reference to oracle bone at all) with oracle glyph embeddings has already been done.

| Work | Year | Approach | Semantic network? | URL |
|---|---|---|---|---|
| **HUST-OBC** | 2024 | Open dataset: 77,064 images / 1,588 deciphered + 62,989 images / 9,411 undeciphered signs | Image-only, no graph | [arXiv:2401.15365](https://arxiv.org/abs/2401.15365) |
| **OBSD** (ACL 2024 Best Paper) | 2024 | Conditional diffusion model generates candidate modern-character glyphs from an oracle glyph | Purely visual, generative | [arXiv:2406.00684](https://arxiv.org/abs/2406.00684) |
| **P3 (Puzzle Pieces Picker)** | 2024 (ICDAR) | Decomposes OBS into strokes/radicals, reconstructs modern counterpart via Transformer | Structural decomposition, not meaning | [arXiv:2406.03019](https://arxiv.org/abs/2406.03019) |
| **RZCR** | 2022/2023 (IJCAI) | Radical identification + reasoning over a Character Knowledge Graph | Graph of radical/structure relations, not curated meanings | [arXiv:2207.05842](https://arxiv.org/abs/2207.05842) |
| **OracleSage** | 2024 | LLaVA-based LVLM + graph-based semantic reasoning framework, new *OracleSem* dataset (1,762 annotated characters) | **Closest to this plan** — but the graph is built from annotating the 1,762 oracle characters themselves | [arXiv:2411.17837](https://arxiv.org/abs/2411.17837) |
| **AlphaOracle** | 2026 | Multi-stage pipeline: rubbing parsing → radical/diachronic morphological analysis → corpus-based semantic alignment → philological validation | "Semantic" = corpus usage, not a decomposition-meaning graph | [arXiv:2607.17849](https://arxiv.org/abs/2607.17849) |

Also surfaced but not yet reviewed in depth: *Interpretable Oracle Bone Script Decipherment through Radical and Pictographic Analysis with LVLMs* ([arXiv:2508.10113](https://arxiv.org/abs/2508.10113)), *OracleFusion* ([arXiv:2506.21101](https://arxiv.org/abs/2506.21101)), *Specializing Large Models for Oracle Bone Script Interpretation via Component-Grounded Multimodal Knowledge Augmentation* ([arXiv:2604.06711](https://arxiv.org/abs/2604.06711)), *OracleAnalyser* ([arXiv:2606.25906](https://arxiv.org/abs/2606.25906)).

Local PDFs of the 6 core papers (HUST-OBC, OBSD, P3, RZCR, OracleSage, AlphaOracle) are kept in `literatures/` for offline reading.

**Finding**: no prior work found pairs an *independently pre-existing, full-lexicon* semantic/decomposition network with oracle glyph embeddings as a decipherment prior. Every semantic/graph component in the literature (OracleSage's GSRF, RZCR's CKG) is built *from* oracle-era annotation effort itself, not imported from a separately-built network spanning the whole modern lexicon. This project's angle — reusing the existing ZiNets decomposition DB as a prior for oracle decipherment — looks genuinely distinct, though OracleSage's graph schema should be read closely before claiming novelty anywhere public.

**Suggestions arising from this search:**

1. **Read `arXiv:2411.17837` (OracleSage) closely** before finalizing the design — it is the one paper close enough to need explicit differentiation, and may have useful schema or evaluation ideas worth borrowing.
2. **Embed jointly, not independently.** The strongest version of the hypothesis is an embedding that aligns or concatenates an image embedding (CLIP/LVLM-style) with a graph embedding of the semantic network (a GNN over `zx_char`/`zx_part`, in the spirit of compositional-graph character-embedding work for modern Chinese). Pure image-embedding nearest-neighbor is already what RZCR and P3 do, without this network's advantage.
3. **Validate on held-out deciphered characters before touching real undeciphered signs.** Hide the decomposition for a sample of already-deciphered characters and check whether adding the semantic-network embedding improves nearest-neighbor accuracy over an image-only baseline. This is the experiment that actually tests whether the network helps, and it is cheap to run with existing HUST-OBC images.
4. **Treat HUST-OBC, OBSD, P3 and RZCR as baselines/comparators**, not just data or reading sources, when evaluating the matching approach.

## Open questions

1. **Which LVLM for embeddings**, and run locally or via API?
   - **Finding (2026-10-02 search):** generic large LVLMs do poorly on oracle glyphs zero-shot — OracleAnalyser's own benchmark has InternVL-3.5-241B at 12.8% and InternVL-3-78B at 7.2% on in-domain oracle bone recognition, versus 39.6% for their post-trained model. Budget for domain adaptation (fine-tuning/LoRA), not zero-shot, whichever backbone is picked.
   - **Candidates, by role:**
     - *Cheapest to try first — pure image-embedding, no generation:* **DINOv2** (Meta, vision-only, no text bottleneck, preserves shape detail well — good fit for glyph-shape nearest-neighbor), **Chinese-CLIP** (Alibaba/OFA-Sys, aligns with Chinese glosses), **SigLIP2** (Google, multilingual zero-shot).
     - *Open LVLMs, if generative/structural reasoning is wanted (captioning components, explaining a match):* **Qwen2.5-VL** (currently strongest open model on Chinese OCR/vision; 7B is a reasonable local size), **InternVL2.5/3** (strong general OCR, but see the weak zero-shot numbers above), **LLaVA** (what OracleSage itself uses — pick this for direct comparability with that paper).
     - *Pattern worth copying instead of reaching for a big LVLM:* several oracle-bone papers train a small **domain-specific encoder** (e.g. a VAE on oracle glyphs only, or a radical-prototype embedding) that outperforms general LVLMs on this narrow domain — consistent with the benchmark gap above.
     - *API models (Claude, GPT-4o/5, Gemini):* fine for quick manual spot-checks on a handful of glyphs, not a good fit for the production pipeline — same domain-gap problem, plus they compound open question 2 (several sources, Wikimedia especially, have unconfirmed image licenses that uploading to a third-party API would make worse, not better).
   - **Suggested starting point:** run the held-out validation from the related-work suggestions (above) with DINOv2 or Chinese-CLIP first — cheapest way to test whether pairing the semantic-network embedding with an image embedding actually helps — before fine-tuning anything larger.
   - Whichever is picked, image resolution/format requirements and licensing exposure (local vs. uploading to a third party) still need deciding.
2. **Licensing per source.** The CSV already flags "check license" for several rows (Wikimedia especially); unlike the CC-CEDICT text attribution already resolved for glosses (`db-integration.md` §5.7), image reuse needs a per-source confirmation before anything is redistributed in this repo.
   - **Checked for the 6 core papers (2026-10-03):**

     | Source | License | Note |
     |---|---|---|
     | HUST-OBC | CC BY-NC 4.0 | Non-commercial research reuse OK, attribution required. Fine for this project. 3 image folders; exclude/quarantine the "GuoXueDaShi" one, flagged unreliable by the authors themselves. |
     | AlphaOracle | Apache-2.0 (code only) | Permissive for code/framework, but the paper states it does **not** redistribute original rubbing images/scans for copyrighted sources — only derived resources (indices, metadata), citing fair use under PRC copyright law. The 73,883-rubbing corpus itself is not reusable as images from this release. |
     | OBSD | none declared | `github.com/guanhaisu/OBSD` has no LICENSE file and no license text in its README — default all-rights-reserved; would need the authors' permission to reuse code or data. |
     | P3 (Puzzle Pieces Picker) | none declared | Same as OBSD: `github.com/Pengjie-W/Puzzle-Pieces-Picker` has no declared license. The ACCP dataset's reuse terms are unstated. |
     | RZCR | not publicly released | No public repo found for the OracleRC dataset; likely available only on request, if at all. |
     | OracleSage | not publicly released | No public repo found for the OracleSem dataset. |

     Net: of the 6, only **HUST-OBC** is clearly reusable as an image source today. AlphaOracle's code is reusable but not its images. The other 4 would need contacting the authors before any reuse.
   - Still open for every other image source in the CSV (Wikimedia, 小學堂, hanziyuan, Wiktionary, 殷契文淵, Academia Sinica IHP).
3. **Where undeciphered signs live**: a new `zx_oracle`/`zx_embedding` pair as sketched above, or a dataset kept entirely outside `zitex.sqlite3` since its purpose (decipherment research) differs from zitex's purpose (typesetting known decompositions)?
4. **Scope relative to zitex's milestone track.** This is not on the M0–M6 list in `docs/DEV/claude/readme.md` (M5/M6 are themselves postponed); decide whether it becomes its own milestone once this plan is reviewed, or stays a separate tool reading `db/zitex.sqlite3` read-only.
5. **Source list completeness** — is `oracle-bone-scripts.csv` final, or are more sources (e.g. additional university corpora) still to be added before pipeline work starts?
