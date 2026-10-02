# Build the demo: zitex scans main.tex, writes snippets, then XeLaTeX typesets them.
#   pip install -e ../..   (once, in the zinets2 env)
ZDATA = ../../tests/data/chars.yaml
ZLEX  = ../../tests/data/lexicon.yaml
# zitex.sty is found through TEXINPUTS here; `zitex install-sty` installs it for good
export TEXINPUTS := ../../src/zitex:

main.pdf: main.tex
	zitex render -i $(ZDATA) --scan main.tex -x $(ZLEX) -l en -l fr --collapse --arrow role
	xelatex -interaction=nonstopmode main.tex

clean:
	rm -rf zitex-out *.aux *.log *.pdf
