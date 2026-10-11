#!/usr/bin/env bash
# Regenerate the snippets (zitex render --scan), then pack the arXiv source: zitex-arxiv-src.tar.gz with main.tex, zitex.sty, flow.pdf, 00README.json (compiler: xelatex),
# the snippets and pictures in zitex-out/, and the font subset in fonts/. Then compile it in a clean folder to check.
#   ./make-arxiv.sh
# The font subset holds only the characters the paper uses. If Noto Serif CJK (the .ttc files) and Python with fontTools
# are available, it is regenerated first, so it always matches the text. Set NOTO_DIR if the fonts are not in
# /usr/share/fonts/opentype/noto, and PYTHON for the interpreter.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
OUT=zitex-arxiv-src.tar.gz
PYTHON="${PYTHON:-python3}"
NOTO_DIR="${NOTO_DIR:-/usr/share/fonts/opentype/noto}"

# the snippets the text asks for are regenerated from the data first, so they cannot lag behind it
REPO="$(cd ../../.. && pwd)"
if [[ -d "$REPO/src/zitex" ]]; then
  PYTHONPATH="$REPO/src${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON" -m zitex render -i chars.yaml --scan main.tex \
    -x lexicon.yaml -x obs/lexicon.yaml -l en -l zh -o zitex-out --strict >/dev/null \
    || { echo "make-arxiv.sh: zitex render failed or reported a missing picture" >&2; exit 1; }
  git checkout -q -- zitex-out/build_manifest.json 2>/dev/null || true
fi

if [[ -f "$NOTO_DIR/NotoSerifCJK-Regular.ttc" ]] && "$PYTHON" -c 'import fontTools' 2>/dev/null; then
  CHARS="$(mktemp)"
  "$PYTHON" - "$CHARS" <<'PY'
import glob, sys
txt = open("main.tex", encoding="utf-8").read()
for f in glob.glob("zitex-out/*.tex"):
    txt += open(f, encoding="utf-8").read()
keep = "".join(chr(i) for i in range(32, 127)) + "".join(sorted({c for c in txt if ord(c) > 0x7f}))
open(sys.argv[1], "w", encoding="utf-8").write(keep)
PY
  for w in Regular Bold; do
    "$PYTHON" -m fontTools.subset "$NOTO_DIR/NotoSerifCJK-$w.ttc" --font-number=2 --text-file="$CHARS" \
      --layout-features='*' --output-file="fonts/NotoSerifCJKsc-Subset-$w.otf"
  done
  rm -f "$CHARS"
else
  echo "make-arxiv.sh: not regenerating the font subset (no Noto Serif CJK .ttc in $NOTO_DIR, or no fontTools)" >&2
fi

rm -f "$OUT"
tar czf "$OUT" --exclude='zitex-out/build_manifest.json' \
  main.tex zitex.sty flow.pdf 00README.json zitex-out fonts
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
tar xzf "$OUT" -C "$TMP"
( cd "$TMP" && xelatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null \
  && xelatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null ) \
  || { echo "make-arxiv.sh: the packed source does not compile" >&2; exit 1; }
if grep -q "Missing character" "$TMP/main.log"; then
  echo "make-arxiv.sh: the packed source compiles but a glyph is missing:" >&2
  grep "Missing character" "$TMP/main.log" | sort -u | head >&2
  exit 1
fi
echo "wrote $(pwd)/$OUT ($(du -h "$OUT" | cut -f1)); it compiles in a clean folder with no missing glyph: $(pdfinfo "$TMP/main.pdf" | grep Pages)"
