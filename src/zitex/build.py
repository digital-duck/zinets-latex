"""Build snippets (and PDFs) for a set of characters; scan a .tex file for what it needs."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .lexicon import Lexicon
from .loader import Entry
from .fonts import FontConfig, svg_to_pdf
from .render import DEFAULT_STYLES, LANG_STYLES, document, math_chars, render_with, split_style

MATH_STYLES = ("math", "pictmath")


def snippet_name(char: str, style: str, lang: str = "en", reading: str | None = None) -> str:
    """File stem used for a snippet: ``u85fb-tree`` (藻 is U+85FB), ``u85fb-math-fr``, ``u8679-math-en@author``.

    The character is named by its code point in lower-case hex, so every file name is plain ASCII and works on any
    file system, in any archive, and with any TeX engine. ``build_manifest.json`` maps the names back to the
    characters. The language is part of the name only for the styles that print glosses, and ``@reading`` only when
    a named reading was asked for. zitex.sty uses the same rule (``\\zitex@name``)."""
    cp = f"u{ord(char):x}"
    stem = f"{cp}-{style}-{lang}" if split_style(style)[0] in LANG_STYLES else f"{cp}-{style}"
    return f"{stem}@{reading}" if reading else stem


# \zi[style=matrix,lang=fr]{藻}  \zimath{藻}  \zitree[reading=author]{藻} ...  and the defaults set with
# \zitexsetlang{fr} / \zitexsetreading{author}
_CALL = re.compile(
    r"\\zitexsetlang\{([^}]*)\}"
    r"|\\zitexsetreading\{([^}]*)\}"
    r"|\\zi(tree|matrix|formula|math)?(?:\[([^\]]*)\])?\{(.)\}"
)


_VERBATIM = re.compile(r"\\begin\{(verbatim\*?|lstlisting|minted)\}.*?\\end\{\1\}", re.S)
_COMMENT = re.compile(r"(?<!\\)%[^\n]*")


def scan_tex(path: str | Path) -> set[tuple[str, str, str | None, str | None]]:
    """(char, style, lang, reading) a .tex file asks for. lang and reading are None when not given.

    Follows the file in order, so a ``\\zitexsetlang{fr}`` or ``\\zitexsetreading{author}`` applies to the
    calls after it, the way zitex.sty applies it. (Grouping is not tracked.) Text LaTeX does not run is skipped:
    ``%`` comments and verbatim, lstlisting and minted blocks, so a listing can show ``\\zitexsetlang{fr}``."""
    found = set()
    lang = reading = None
    text = _COMMENT.sub("", _VERBATIM.sub("", Path(path).read_text(encoding="utf-8")))
    for m in _CALL.finditer(text):
        if m.group(1) is not None:
            lang = m.group(1).strip() or None
        elif m.group(2) is not None:
            reading = m.group(2).strip() or None
        else:
            style, opts, ch = m.group(3), m.group(4) or "", m.group(5)
            items = [x.strip() for x in opts.split(",") if x.strip()]
            kv = {k.strip(): v.strip() for k, v in (p.split("=", 1) for p in items if "=" in p)}
            st = style or kv.get("style", "tree")
            pict = kv.get("pict", "true" if "pict" in items else "false")
            if st == "math" and pict != "false":     # \zimath[pict]{字}: the grid with a picture row
                st = "pictmath" if pict == "true" else f"pictmath-{pict}"   # [pict=obs]: the set of pictures obs
            found.add((ch, st, kv.get("lang", lang), kv.get("reading", reading)))
    return found


@dataclass
class BuildResult:
    tex: list[Path] = field(default_factory=list)
    pdf: list[Path] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)   # characters not found in the data
    failed: list[str] = field(default_factory=list)    # PDF builds that did not compile
    glyph_missing: list[str] = field(default_factory=list)  # components no font or image could draw
    manifest: list[dict] = field(default_factory=list)      # one record per snippet, see write_manifest()
    pict_problems: list[str] = field(default_factory=list)  # pictures asked for that could not be made
    no_pict: list[str] = field(default_factory=list)        # "set: parts" with no picture (an empty cell)


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
            tail = "\n".join((r.stdout or "").strip().splitlines()[-8:])
            print(f"xelatex failed for {dest.name}:\n{tail}", file=sys.stderr)
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
        jobs = {(c, s, l, reading) for c in (chars or list(by_char)) for s in (styles or DEFAULT_STYLES) for l in langs}
    jobs = {(c, st, l if split_style(st)[0] in LANG_STYLES else langs[0], rd) for c, st, l, rd in jobs}   # tree/matrix: one file whatever -l
    res = BuildResult()
    converted: set[str] = set()
    for ch, style, lang, rd in sorted(jobs, key=lambda j: tuple(x or "" for x in j)):
        e = by_char.get(ch)
        if e is None:
            if ch not in res.missing:
                res.missing.append(ch)
            continue
        base, pict_set = split_style(style)
        kw = dict(math_opts or {}) if base in MATH_STYLES else {}
        if base in LANG_STYLES:
            kw["lang"], kw["lex"] = lang, lex
        stem = snippet_name(ch, style, lang, rd)
        snippet, resolver = render_with(e, style, fonts, reading=rd, **kw)
        picts = lex.stage_picts(math_chars(e), outdir, pict_set) if base == "pictmath" and lex else []
        bare = [c for c in dict.fromkeys(math_chars(e)) if lex.pict_name(c, pict_set) is None] if base == "pictmath" and lex else []
        if bare:
            res.no_pict.append(f"{style} {ch}: {' '.join(bare)}")
        record = {"char": ch, "codepoint": f"U+{ord(ch):04X}", "style": style, "lang": lang if base in LANG_STYLES else None,
                  "reading": rd, "file": f"{stem}.pdf" if emit == "pdf" else f"{stem}.tex", "fallback_fonts": [], "images": [], "no_glyph": [], "picts": picts, "parts_without_pict": bare}
        if resolver:
            record.update(fallback_fonts=sorted(resolver.fonts), images=sorted(Path(s).name for s in resolver.svgs),
                          no_glyph=sorted(resolver.missing))
            for m in resolver.missing:
                if m not in res.glyph_missing:
                    res.glyph_missing.append(m)
            for svg in resolver.svgs - converted:
                src = Path(svg) if Path(svg).is_absolute() else fonts.base / svg
                svg_to_pdf(src, outdir / "glyphs" / f"{src.stem}.pdf")
                converted.add(svg)
        if emit in ("tex", "both"):
            p = outdir / f"{stem}.tex"
            p.write_text(snippet + "\n", encoding="utf-8")
            res.tex.append(p)
        res.manifest.append(record)
        if emit in ("pdf", "both"):
            p = outdir / f"{stem}.pdf"
            (res.pdf if compile_pdf(snippet, p, font, str(outdir.resolve())) else res.failed).append(p if p.exists() else Path(stem))
    if lex:
        res.pict_problems = sorted(lex.problems)
    write_manifest(res, outdir)
    return res


def write_manifest(res: BuildResult, outdir: str | Path) -> Path:
    """``build_manifest.json``: what this build wrote, for audits and for finding a snippet by its character.

    One record per snippet (the character, its code point, style, language, reading, file name, the fallback fonts
    and images it uses, and any component nothing could draw), then the characters that were not in the data and
    the components without a glyph, over the whole build. It describes the latest build in the folder: a later
    build overwrites it."""
    from . import __version__
    doc = {"zitex_version": __version__, "snippets": res.manifest, "characters_not_in_data": res.missing,
           "components_without_glyph": res.glyph_missing, "picture_problems": res.pict_problems, "pdf_failed": [p.name for p in res.failed]}
    path = Path(outdir) / "build_manifest.json"
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path
