#!/usr/bin/env bash
# Build main.pdf: zitex scans main.tex and writes the snippets and pictures, then XeLaTeX typesets them.
#   ./build.sh          build main.pdf: 明 and 虹 with emoji picts, and with oracle bone glyphs (pict=obs)
#   ./build.sh clean    remove zitex-out/ and the LaTeX files
# Needs xelatex, and Pillow for the emoji picts.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
REPO="$(cd ../.. && pwd)"

if [[ "${1:-}" == "clean" ]]; then
  rm -rf zitex-out main.aux main.log main.pdf
  exit 0
fi

# the installed `zitex` command, else run it from the checkout
if command -v zitex >/dev/null 2>&1; then
  ZITEX=(zitex)
else
  export PYTHONPATH="$REPO/src${PYTHONPATH:+:$PYTHONPATH}"
  ZITEX=("${PYTHON:-python3}" -m zitex)
fi
# zitex.sty is found through TEXINPUTS here; `zitex install-sty` installs it for good
export TEXINPUTS="$REPO/src/zitex:${TEXINPUTS:-}"

command -v xelatex >/dev/null 2>&1 || { echo "build.sh: xelatex not found" >&2; exit 1; }

# obs/lexicon.yaml adds the picture set obs (oracle bone glyphs exported from Orascope) to the emoji of lexicon.yaml
"${ZITEX[@]}" render -i chars.yaml --scan main.tex -x lexicon.yaml -x obs/lexicon.yaml -l en -l zh
xelatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null || { echo "build.sh: xelatex failed, see main.log" >&2; exit 1; }
echo "wrote $(pwd)/main.pdf"
