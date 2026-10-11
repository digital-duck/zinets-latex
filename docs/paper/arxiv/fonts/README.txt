NotoSerifCJKsc-Subset-Regular.otf and -Bold.otf are subsets of Noto Serif CJK SC
(https://github.com/googlefonts/noto-cjk), cut down to the characters this paper uses so the
submission compiles with the same glyphs on any machine. Noto Serif CJK is licensed under the
SIL Open Font License 1.1 (https://openfontlicense.org); the licence text is in OFL.txt in this folder. The font's own copyright
line reads "(c) 2017-2022 Adobe (http://www.adobe.com/)"; "Noto" is a trademark of Google LLC. The fonts were modified only by subsetting.
Regenerate with:  python -m fontTools.subset NotoSerifCJK-Regular.ttc --font-number=2 --text-file=chars.txt \
                    --layout-features='*' --output-file=NotoSerifCJKsc-Subset-Regular.otf
