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


def snippet_name(char: str, style: str, lang: str = "en", reading: str | None = None) -> str:
    """File stem used for a snippet: ``藻-tree``, ``藻-math-fr``, ``虹-math-en@author``.

    The language is part of the name only for the styles that print glosses, and ``@reading`` only when a
    named reading was asked for. zitex.sty uses the same rule."""
    stem = f"{char}-{style}-{lang}" if style in LANG_STYLES else f"{char}-{style}"
    return f"{stem}@{reading}" if reading else stem


# \zi[style=matrix,lang=fr]{藻}  \zimath{藻}  \zitree[reading=author]{藻} ...  and the defaults set with
# \zitexsetlang{fr} / \zitexsetreading{author}
_CALL = re.compile(
    r"\\zitexsetlang\{([^}]*)\}"
    r"|\\zitexsetreading\{([^}]*)\}"
    r"|\\zi(tree|matrix|formula|math)?(?:\[([^\]]*)\])?\{(.)\}"
)


def scan_tex(path: str | Path) -> set[tuple[str, str, str | None, str | None]]:
    """(char, style, lang, reading) a .tex file asks for. lang and reading are None when not given.

    Follows the file in order, so a ``\\zitexsetlang{fr}`` or ``\\zitexsetreading{author}`` applies to the
    calls after it, the way zitex.sty applies it. (Grouping is not tracked.)"""
    found = set()
    lang = reading = None
    for m in _CALL.finditer(Path(path).read_text(encoding="utf-8")):
        if m.group(1) is not None:
            lang = m.group(1).strip() or None
        elif m.group(2) is not None:
            reading = m.group(2).strip() or None
        else:
            style, opts, ch = m.group(3), m.group(4) or "", m.group(5)
            kv = dict(p.split("=", 1) for p in (x.strip() for x in opts.split(",")) if "=" in p)
            found.add((ch, style or kv.get("style", "tree"), kv.get("lang", lang), kv.get("reading", reading)))
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


def write_snippet(snippet: str, resolver, fonts: FontConfig | None, stem: Path, emit: str = "tex",
                  font: str | None = None) -> tuple[Path | None, Path | None, bool]:
    """Write one snippet as ``STEM.tex`` and/or ``STEM.pdf`` (``stem`` is a path without a suffix).

    Returns (tex path or None, pdf path or None, ok). ok is False when the PDF did not compile.
    SVG glyphs the snippet uses are converted into ``<stem's folder>/glyphs``."""
    if emit not in ("tex", "pdf", "both"):
        raise ValueError("emit must be tex, pdf or both")
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    font = font or (fonts.primary if fonts else "Noto Serif CJK SC")
    if resolver and fonts:
        for svg in resolver.svgs:
            src = Path(svg) if Path(svg).is_absolute() else fonts.base / svg
            svg_to_pdf(src, stem.parent / "glyphs" / f"{src.stem}.pdf")
    tex = pdf = None
    ok = True
    if emit in ("tex", "both"):
        tex = stem.with_name(stem.name + ".tex")
        tex.write_text(snippet + "\n", encoding="utf-8")
    if emit in ("pdf", "both"):
        pdf = stem.with_name(stem.name + ".pdf")
        ok = compile_pdf(snippet, pdf, font, str(stem.parent.resolve()))
        pdf = pdf if ok else None
    return tex, pdf, ok


def build(entries: list[Entry], outdir: str | Path, jobs: set[tuple[str, str, str, str | None]] | None = None, *,
          chars: list[str] | None = None, styles: list[str] | None = None, langs: list[str] | None = None,
          emit: str = "tex", lex: Lexicon | None = None, font: str | None = None,
          math_opts: dict | None = None, fonts: FontConfig | None = None, reading: str | None = None) -> BuildResult:
    """Render snippets into outdir.

    jobs:  explicit (char, style, lang, reading) tuples (from scan_tex). Otherwise chars x styles x langs, all
           under `reading` (a named reading of the roles; entries without it use their default).
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
        jobs = {(c, s, l, reading) for c in (chars or list(by_char)) for s in (styles or list(STYLES)) for l in langs}
    jobs = {(c, st, l if st in LANG_STYLES else langs[0], rd) for c, st, l, rd in jobs}   # tree/matrix: one file whatever -l
    res = BuildResult()
    converted: set[str] = set()
    for ch, style, lang, rd in sorted(jobs, key=lambda j: tuple(x or "" for x in j)):
        e = by_char.get(ch)
        if e is None:
            if ch not in res.missing:
                res.missing.append(ch)
            continue
        kw = dict(math_opts or {}) if style == "math" else {}
        if style in LANG_STYLES:
            kw["lang"], kw["lex"] = lang, lex
        stem = snippet_name(ch, style, lang, rd)
        snippet, resolver = render_with(e, style, fonts, reading=rd, **kw)
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
