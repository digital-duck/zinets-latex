"""The files of a zitex working folder: what `zitex setup` writes, and the main.tex that `zitex extract` writes.

A working folder holds zitex.sty, fonts.yaml, fallback.yaml and glyphs/ (from setup), then chars.yaml, lexicon.yaml,
main.tex and zitex-out/ (from extract). `xelatex main.tex` in that folder typesets the result, and the folder is
self-contained: LaTeX finds zitex.sty next to main.tex, so nothing is installed anywhere else.
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from .fonts import DEFAULT_PRIMARY, FontChoice
from .render import esc

TEMPLATES = Path(__file__).with_name("templates")
STY = Path(__file__).with_name("zitex.sty")
MAX_CHARS = 60           # `zitex extract` keeps at most this many characters: more would make main.tex a book


def fonts_yaml_text(choice: FontChoice) -> str:
    primary = choice.primary or DEFAULT_PRIMARY
    if choice.primary is None:
        note = (f"# WARNING: none of the usual CJK fonts was found, so this names {DEFAULT_PRIMARY}. Install it, or change "
                "`primary` to a CJK font you have (fc-list :lang=zh).")
    else:
        note = f"# The primary font was found on this computer and has {choice.primary_size:,} CJK characters."
    fb = ", ".join(json.dumps(f, ensure_ascii=False) for f, _ in choice.fallbacks)
    fb_note = ("; ".join(f"{f} adds {n:,}" for f, n in choice.fallbacks)) or "no installed font adds characters to the primary"
    return f"""# Fonts for zitex. Made by `zitex setup` from the fonts installed on this computer.
{note}
#
# primary:    the main CJK font. main.tex sets it with \\setCJKmainfont, and zitex checks every component against it,
#             so the two must name the same font.
# fallbacks:  tried in order when the primary font has no glyph for a component.
#             Chosen here: {fb_note}.
# components: overrides for single components: an image (svg), a font, or an alias to another character.
primary: {json.dumps(primary, ensure_ascii=False)}
fallbacks: [{fb}]
components:
  "{{demo}}": {{svg: glyphs/demo.svg}}      # a placeholder for a component with no Unicode code point (needs inkscape)
  # 甲: {{alias: 日}}                      # draw another character instead
  # 𠀉: {{font: Some Font}}                # force a font for one component
"""


@dataclass
class SetupResult:
    written: list[Path] = field(default_factory=list)
    kept: list[Path] = field(default_factory=list)          # existing files left alone
    sty: str = ""                                           # "installed", "updated" or "up to date"


def write_setup(out: Path, choice: FontChoice, force: bool = False) -> SetupResult:
    """Write zitex.sty, fonts.yaml, fallback.yaml and glyphs/demo.svg into `out`.

    fonts.yaml, fallback.yaml and glyphs/ may be edited, so an existing one is kept unless `force` is set. zitex.sty
    is not for editing: it has to match this version of zitex (it defines the names of the snippet files), so it is
    brought up to date whenever it differs.
    """
    out.mkdir(parents=True, exist_ok=True)
    res = SetupResult()
    sty = out / "zitex.sty"
    if sty.is_file() and sty.read_bytes() == STY.read_bytes():
        res.sty = "up to date"
    else:
        res.sty = "updated" if sty.is_file() else "installed"
        shutil.copyfile(STY, sty)
        res.written.append(sty)
    plan = [
        (out / "fonts.yaml", fonts_yaml_text(choice)),
        (out / "fallback.yaml", (TEMPLATES / "fallback.yaml").read_text(encoding="utf-8")),
        (out / "glyphs" / "demo.svg", (TEMPLATES / "demo.svg").read_text(encoding="utf-8")),
    ]
    for path, text in plan:
        if path.exists() and not force:
            res.kept.append(path)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        res.written.append(path)
    return res


def sty_state(out: Path) -> str:
    """"local" (zitex.sty is in the folder and matches this zitex), "stale" (it differs), or "absent"."""
    sty = out / "zitex.sty"
    if not sty.is_file():
        return "absent"
    return "local" if sty.read_bytes() == STY.read_bytes() else "stale"


ANNOTATIONS = ("minimal", "demo")   # the values of `zitex extract --annotation`
GALLERY_ROWS = 8         # the gallery table shows at most this many characters; the catalogue lists them all


def make_main_tex(dicts: list[dict], primary: str, annotation: str = "minimal") -> str:
    """The main.tex that `zitex extract` writes, filled in for the extracted characters.

    The template is templates/main.tex ("minimal": every style for every character, like examples/demo) or
    templates/demo.tex ("demo": an annotated paper). They share the @@NAME@@ placeholders they use. In the demo
    the first character is the example for the four views, and the second is the other one in the figure (the first
    again, when there is only one); the gallery table takes up to GALLERY_ROWS characters, and the catalogue all.
    """
    if annotation not in ANNOTATIONS:
        raise ValueError(f"annotation must be one of {', '.join(ANNOTATIONS)}, not {annotation!r}")
    chars = [d["char"] for d in dicts]
    first, second = chars[0], chars[1] if len(chars) > 1 else chars[0]
    rows = [rf"    {c} & \resizebox{{0.40\linewidth}}{{!}}{{\zimatrix{{{c}}}}} & \ziformula{{{c}}}\unskip \\[4pt]"
            for c in chars[:GALLERY_ROWS]]
    more = f" (the first {GALLERY_ROWS} of {len(chars)})" if len(chars) > GALLERY_ROWS else ""
    catalogue = []
    for d in dicts:
        ch = d["char"]
        label = ", ".join(esc(x) for x in (d.get("pinyin"), d.get("meaning")) if x)
        catalogue += [
            rf"\subsection*{{{ch}" + (rf" \normalfont\small({label})" if label else "") + "}",
            rf"\zimath{{{ch}}}", "",
            rf"\zimatrix{{{ch}}}\qquad\ziformula{{{ch}}}", "",
            rf"\zitree{{{ch}}}", "",
        ]
    fill = {"@@PRIMARY@@": primary, "@@CHARS@@": " ".join(chars), "@@A@@": first, "@@B@@": second,
            "@@GALLERY_INTRO@@": f"The characters {' '.join(chars[:GALLERY_ROWS])}{more}",
            "@@GALLERY_ROWS@@": "\n".join(rows), "@@CATALOGUE@@": "\n".join(catalogue).rstrip(), "@@CLIST@@": ",".join(chars)}
    tex = (TEMPLATES / ("demo.tex" if annotation == "demo" else "main.tex")).read_text(encoding="utf-8")
    for key, value in fill.items():
        tex = tex.replace(key, value)
    return tex
