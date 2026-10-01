# Build the demo: zitex scans main.tex, writes snippets, then XeLaTeX typesets them.
#   pip install -e ../..   (once, in the zinets2 env)
ZDATA = ../../tests/data/chars.yaml
ZLEX  = ../../tests/data/lexicon.yaml
export TEXINPUTS := ../../tex:

main.pdf: main.tex
	zitex build $(ZDATA) --scan main.tex -x $(ZLEX) -l en -l fr --collapse --arrow role -o zitex-out
	xelatex -interaction=nonstopmode main.tex

clean:
	rm -rf zitex-out *.aux *.log *.pdf
