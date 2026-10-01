"""Build snippets (and PDFs) for a set of characters; scan a .tex file for what it needs."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .lexicon import Lexicon
from .loader import Entry
from .fonts import FontConfig, svg_to_pdf
from .render import STYLES, document, render_with

LANG_STYLES = ("math", "formula")  # styles whose output depends on the language


def snippet_name(char: str, style: str, lang: str = "en") -> str:
    """File stem used for a snippet, e.g. ``藻-tree`` or ``藻-math-fr``. zitex.sty uses the same rule."""
    return f"{char}-{style}-{lang}" if style in LANG_STYLES else f"{char}-{style}"


# \zi[style=matrix,lang=fr]{藻}  \zimath{藻}  \zitree[lang=fr]{藻} ...
_CALL = re.compile(r"\\zi(tree|matrix|formula|math)?(?:\[([^\]]*)\])?\{(.)\}")


def scan_tex(path: str | Path) -> set[tuple[str, str, str | None]]:
    """(char, style, lang) triples a .tex file asks for. lang is None when not given."""
    found = set()
    for m in _CALL.finditer(Path(path).read_text(encoding="utf-8")):
        style, opts, ch = m.group(1), m.group(2) or "", m.group(3)
        kv = dict(p.split("=", 1) for p in (x.strip() for x in opts.split(",")) if "=" in p)
        found.add((ch, style or kv.get("style", "tree"), kv.get("lang")))
    return found


@dataclass
class BuildResult:
    tex: list[Path] = field(default_factory=list)
    pdf: list[Path] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)   # characters not found in the data
    failed: list[str] = field(default_factory=list)    # PDF builds that did not compile
    glyph_missing: list[str] = field(default_factory=list)  # components no font or image could draw


def compile_pdf(snippet: str, dest: Path, font: str = "Noto Serif CJK SC", zitexpath: str | None = None) -> bool:
    """Compile one snippet with XeLaTeX into dest (a .pdf path)."""
    if shutil.which("xelatex") is None:
        raise RuntimeError("xelatex not found")
    with tempfile.TemporaryDirectory() as tmp:
        tex = Path(tmp) / "fig.tex"
        tex.write_text(document(snippet, font=font, zitexpath=zitexpath), encoding="utf-8")
        r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error",
                            "-output-directory", tmp, str(tex)], capture_output=True, text=True)
        pdf = Path(tmp) / "fig.pdf"
        if r.returncode != 0 or not pdf.exists():
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pdf, dest)
        return True


def build(entries: list[Entry], outdir: str | Path, jobs: set[tuple[str, str, str]] | None = None, *,
          chars: list[str] | None = None, styles: list[str] | None = None, langs: list[str] | None = None,
          emit: str = "tex", lex: Lexicon | None = None, font: str | None = None,
          math_opts: dict | None = None, fonts: FontConfig | None = None) -> BuildResult:
    """Render snippets into outdir.

    jobs:  explicit (char, style, lang) triples (from scan_tex). Otherwise chars x styles x langs.
    emit:  "tex" (snippets), "pdf" (compiled figures) or "both".
    fonts: glyph fallback configuration (see zitex.fonts). The CJK font is fonts.primary unless `font` is given.
    """
    font = font or (fonts.primary if fonts else "Noto Serif CJK SC")
    if emit not in ("tex", "pdf", "both"):
        raise ValueError("emit must be tex, pdf or both")
    by_char = {e.char: e for e in entries}
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    langs = langs or ["en"]
    if jobs is None:
        jobs = {(c, s, l) for c in (chars or list(by_char)) for s in (styles or list(STYLES)) for l in langs}
    res = BuildResult()
    converted: set[str] = set()
    for ch, style, lang in sorted(jobs):
        e = by_char.get(ch)
        if e is None:
            if ch not in res.missing:
                res.missing.append(ch)
            continue
        kw = dict(math_opts or {}) if style == "math" else {}
        if style in LANG_STYLES:
            kw["lang"], kw["lex"] = lang, lex
        stem = snippet_name(ch, style, lang)
        snippet, resolver = render_with(e, style, fonts, **kw)
        if resolver:
            for ch in resolver.missing:
                if ch not in res.glyph_missing:
                    res.glyph_missing.append(ch)
            for svg in resolver.svgs - converted:
                src = Path(svg) if Path(svg).is_absolute() else fonts.base / svg
                svg_to_pdf(src, outdir / "glyphs" / f"{src.stem}.pdf")
                converted.add(svg)
        if emit in ("tex", "both"):
            p = outdir / f"{stem}.tex"
            p.write_text(snippet + "\n", encoding="utf-8")
            res.tex.append(p)
        if emit in ("pdf", "both"):
            p = outdir / f"{stem}.pdf"
            (res.pdf if compile_pdf(snippet, p, font, str(outdir.resolve())) else res.failed).append(p if p.exists() else Path(stem))
    return res
