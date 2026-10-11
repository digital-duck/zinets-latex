#!/usr/bin/env bash
# Pack the arXiv source: zitex-arxiv-src.tar.gz with main.tex, zitex.sty, flow.pdf, 00README.json (compiler: xelatex),
# the snippets and pictures in zitex-out/, and the font subset in fonts/. Then compile it in a clean folder to check.
#   ./make-arxiv.sh
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
OUT=zitex-arxiv-src.tar.gz
rm -f "$OUT"
tar czf "$OUT" --exclude='zitex-out/build_manifest.json' \
  main.tex zitex.sty flow.pdf 00README.json zitex-out fonts
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
tar xzf "$OUT" -C "$TMP"
( cd "$TMP" && xelatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null \
  && xelatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null ) \
  || { echo "make-arxiv.sh: the packed source does not compile" >&2; exit 1; }
echo "wrote $(pwd)/$OUT ($(du -h "$OUT" | cut -f1)); it compiles in a clean folder: $(pdfinfo "$TMP/main.pdf" | grep Pages)"
