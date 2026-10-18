# Examples

| Folder | What it shows |
|---|---|
| `demo/` | the demo paper: scan, render and typeset with XeLaTeX (`make -C examples/demo`) |
| `m2/` | single characters in each view (tree, matrix, equations, formulas) |
| `pict/` | `\zimath[pict]`: pinyin, character, meaning and a picture per term, including oracle bone, bronze, seal and kaiti forms (`./build.sh`) |

## Data and images: demo use only

The glyph images in `pict/` come from two outside sources, and they are here **only to demonstrate zitex**. They are
**not for redistribution**, and they are not covered by the MIT licence of the zitex code.

- **HUST-OBC** (oracle bone script, https://github.com/Pengjie-W/HUST-OBC): CC BY-NC 4.0, so attribution is required
  and use must be non-commercial. Source images are listed in `pict/obs/picts.csv`, with the licence text in
  `pict/obs/LICENSE`.
- **hanziyuan.net** (bronze, seal and kaiti forms, via hanziyuan-app): used with no licence stated. The rights stay with
  the site and its own sources.

Do not copy these images into other projects, datasets or packages. They are not included in the PyPI package. To
use them beyond a demo, ask the owners for permission. See also the `NOTICE` file at the root of the repository.
