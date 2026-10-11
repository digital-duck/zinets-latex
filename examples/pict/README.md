# \zimath[pict]: sound, shape and meaning in one equation

    ./build.sh                # scan, render and typeset: writes main.pdf and main-obs.pdf (./build.sh clean removes them)

or by hand:

    zitex render -i chars.yaml --scan main.tex -x lexicon.yaml -l en -l zh
    xelatex main.tex          # zitex.sty found via TEXINPUTS or `zitex install-sty`

Per character, top to bottom: pinyin, the character, its meaning (concrete gloss, else `concept`, else
`category`, else nothing), then the pict (a small image from `ZITEX_PICT_DIR` or the lexicon, else an emoji,
else nothing). The lexicon here uses emoji; `data/ele_chars/` holds oracle bone glyphs exported from Orascope
(`scripts/export_picts.py`) and a matching `lexicon.yaml`.

What `main.tex` shows (`./build.sh` writes `main.pdf`):

1. **Emoji as the pict**, from `lexicon.yaml`: 日 + 月 = 明 in English and in Chinese (`lang=zh`), and 虫 + 工 = 虹.
2. **Oracle bone glyphs as the pict**: the same equations with `\zimath[pict=obs,lang=zh]{…}`. `pict=obs` names a set of pictures: the
   lexicon key `pict_obs`, defined in `obs/lexicon.yaml`. The glyphs are in `obs/` (`u<hex>.png`, with `picts.csv` recording the
   HUST-OBC source image of each). They were exported from Orascope with
   `python scripts/export_picts.py --dest ../zinets-latex/examples/pict/obs --chars 日月明虫工虹 --set obs`.
   `build.sh` passes `obs/lexicon.yaml` after `lexicon.yaml`, so it adds the set without touching the glosses.

HUST-OBC is CC BY-NC 4.0: keep the attribution. Note that most oracle bone forms of 明 show a moon and a window (囧), not a sun.
