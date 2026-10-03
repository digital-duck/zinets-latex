"""Glyph coverage and fallback: which font (or image) draws each component.

fonts.yaml::

    primary: Noto Serif CJK SC          # default CJK font of the document
    fallbacks: [AR PL UMing CN, Unifont Upper]   # tried in order when the primary lacks a glyph
    components:                         # explicit per-component overrides
      "{qi-top}": {svg: glyphs/qi-top.svg}       # component with no Unicode code point
      𠀉: {font: Unifont Upper}
      甲: {alias: 日}                              # draw this other character instead

Resolution order for a component: override, primary font, fallback fonts, then a boxed label
(reported as missing). Components longer than one character are names, written ``{name}`` in a shape string.
"""
from __future__ import annotations

import contextvars
import shutil
import subprocess
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from . import config as cfg

DEFAULT_PRIMARY = "Noto Serif CJK SC"


@lru_cache(maxsize=None)
def _font_files() -> dict[str, tuple[str, int]]:
    """family name -> (file, index), from fontconfig."""
    if shutil.which("fc-list") is None:
        return {}
    out = subprocess.run(["fc-list", "-f", "%{file}|%{index}|%{family}\\n"], capture_output=True, text=True).stdout
    found: dict[str, tuple[str, int]] = {}
    for line in out.splitlines():
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        f, idx, fam = parts
        for name in fam.split(","):
            found.setdefault(name.strip(), (f, int(idx) & 0xFFFF))
    return found


@lru_cache(maxsize=None)
def cmap(family: str) -> frozenset[int] | None:
    """Code points a font family covers, or None if the family or fontTools is unavailable."""
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return None
    hit = _font_files().get(family)
    if not hit:
        return None
    try:
        return frozenset(TTFont(hit[0], fontNumber=hit[1], lazy=True).getBestCmap())
    except Exception:
        return None


def covers(family: str, ch: str) -> bool | None:
    """True/False if known, None when the font cannot be inspected."""
    cm = cmap(family)
    return None if cm is None else (len(ch) == 1 and ord(ch) in cm)


def _bare(key: str) -> str:
    """``{name}`` -> ``name`` (components are written with braces in a shape string but stored without)."""
    return key[1:-1] if len(key) > 2 and key[0] == "{" and key[-1] == "}" else key


@dataclass
class FontConfig:
    primary: str = DEFAULT_PRIMARY
    fallbacks: list[str] = field(default_factory=list)
    components: dict[str, dict] = field(default_factory=dict)
    base: Path = Path(".")  # directory fonts.yaml lives in; svg paths are relative to it

    @classmethod
    def load(cls, path: str | Path) -> "FontConfig":
        p = Path(path)
        d = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return cls(primary=d.get("primary", DEFAULT_PRIMARY), fallbacks=list(d.get("fallbacks") or []),
                   components={_bare(k): v for k, v in (d.get("components") or {}).items()}, base=p.parent)


@dataclass
class Resolution:
    kind: str            # plain | font | svg | alias | missing
    value: str = ""      # font family, svg file, alias text


def resolve(cfg: FontConfig, ch: str) -> Resolution:
    over = cfg.components.get(ch)
    if over:
        if "svg" in over:
            return Resolution("svg", str(over["svg"]))
        if "alias" in over:
            return Resolution("alias", str(over["alias"]))
        if "font" in over:
            return Resolution("font", str(over["font"]))
    if len(ch) != 1:                      # a name with no override: nothing to draw
        return Resolution("missing")
    ok = covers(cfg.primary, ch)
    if ok is None or ok:                  # unknown means "assume covered": never break a build on a guess
        return Resolution("plain")
    for fb in cfg.fallbacks:
        if covers(fb, ch):
            return Resolution("font", fb)
    return Resolution("missing")


# ---- used by the renderers --------------------------------------------------

PRELUDE = "\n".join([
    r"\providecommand\zitexpath{zitex-out}",
    r"\providecommand\zifont[3]{{\expandafter\ifx\csname zifam@#1\endcsname\relax"
    r"\setCJKfamilyfont{zifam@#1}{#2}\expandafter\gdef\csname zifam@#1\endcsname{}\fi\CJKfamily{zifam@#1}#3}}",
    r"\providecommand\zisvg[1]{\raisebox{" + cfg.IMAGE_GLYPH_RAISE + r"}{\includegraphics[height=" + cfg.IMAGE_GLYPH_HEIGHT
    + r"]{\zitexpath/glyphs/#1}}}",
    r"\providecommand\zimissing[1]{\fbox{" + cfg.MISSING_GLYPH_FONT + " #1}}",
])


class Resolver:
    """Per-render glyph resolver. Collects what it used so the snippet can carry what it needs."""

    def __init__(self, cfg: FontConfig):
        self.cfg = cfg
        self.fonts: dict[str, int] = {}
        self.used = False
        self.missing: set[str] = set()
        self.svgs: set[str] = set()

    def glyph(self, ch: str) -> str:
        r = resolve(self.cfg, ch)
        if r.kind == "plain":
            return ch
        self.used = True
        if r.kind == "alias":
            return self.glyph(r.value) if r.value != ch else r.value
        if r.kind == "font":
            n = self.fonts.setdefault(r.value, len(self.fonts) + 1)
            return rf"\zifont{{{n}}}{{{r.value}}}{{{ch}}}"
        if r.kind == "svg":
            self.svgs.add(r.value)
            return rf"\zisvg{{{Path(r.value).stem}.pdf}}"
        self.missing.add(ch)
        label = f"U+{ord(ch):04X}" if len(ch) == 1 else ch   # a bare glyph would not render either
        return rf"\zimissing{{{label}}}"

    @property
    def prelude(self) -> str:
        return PRELUDE if self.used else ""


CURRENT: contextvars.ContextVar[Resolver | None] = contextvars.ContextVar("zitex_resolver", default=None)


def svg_to_pdf(svg: Path, dest: Path) -> None:
    """Convert an SVG glyph to PDF (Inkscape) so XeLaTeX can include it."""
    exe = shutil.which("inkscape")
    if exe is None:
        raise RuntimeError("inkscape is needed to convert SVG glyphs to PDF")
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([exe, str(svg), "--export-type=pdf", f"--export-filename={dest}"], capture_output=True, text=True)
    if r.returncode != 0 or not dest.exists():
        raise RuntimeError(f"inkscape failed on {svg}: {r.stderr[-300:]}")


# ---- coverage report --------------------------------------------------------

@dataclass
class Report:
    rows: list[tuple[str, Resolution, list[str]]]  # component, how drawn, characters using it
    inspected: bool

    @property
    def missing(self) -> list[str]:
        return [c for c, r, _ in self.rows if r.kind == "missing"]


def coverage_report(entries, cfg: FontConfig) -> Report:
    from .tree import leaves
    users: dict[str, list[str]] = {}
    for e in entries:
        for ch in {e.char} | {l.c for l in leaves(e.tree) if l.c}:
            users.setdefault(ch, []).append(e.char)
    rows = sorted(((c, resolve(cfg, c), u) for c, u in users.items()), key=lambda r: (r[1].kind != "missing", r[0]))
    return Report(rows, cmap(cfg.primary) is not None)


# ---- finding fonts on this computer (used by `zitex setup`) ------------------------------------------------

PRIMARY_CANDIDATES = ("Noto Serif CJK SC", "Noto Serif CJK TC", "Noto Serif CJK JP", "Source Han Serif SC",
                      "Noto Sans CJK SC", "Source Han Sans SC", "WenQuanYi Zen Hei", "AR PL UMing CN",
                      "Droid Sans Fallback")
FALLBACK_CANDIDATES = ("Noto Sans CJK SC", "Noto Serif CJK TC", "Noto Serif CJK JP", "Noto Serif CJK KR",
                       "Noto Serif CJK HK", "Source Han Serif SC", "Source Han Sans SC", "AR PL UMing CN",
                       "AR PL UMing TW", "WenQuanYi Zen Hei", "Droid Sans Fallback", "Unifont", "Unifont Upper",
                       "BabelStone Han", "HanaMin", "Hanazono Mincho A", "Hanazono Mincho B", "Sun-ExtA", "SimSun-ExtB")
_CJK_RANGES = ((0x2E80, 0x2FDF), (0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF), (0x20000, 0x2FA1F))


def _cjk(codes) -> set[int]:
    return {c for c in codes if any(a <= c <= b for a, b in _CJK_RANGES)}


@dataclass
class FontChoice:
    primary: str | None                                   # None: none of the candidates is installed
    fallbacks: list[tuple[str, int]] = field(default_factory=list)   # (family, CJK characters it adds)
    primary_size: int = 0                                 # CJK characters the primary font has


def detect_fonts() -> FontChoice:
    """The primary font is the first installed candidate. The fallbacks are chosen greedily: each one is the
    installed font that adds the most CJK characters that nothing chosen so far has, and a font that adds none
    is left out. Needs fontconfig and fontTools; without them nothing is found."""
    installed = _font_files()
    primary = next((f for f in PRIMARY_CANDIDATES if f in installed and cmap(f) is not None), None)
    if primary is None:
        return FontChoice(None)
    have = _cjk(cmap(primary) or ())
    choice = FontChoice(primary, [], len(have))
    pool = {f: _cjk(cmap(f) or ()) for f in FALLBACK_CANDIDATES if f in installed and f != primary}
    while pool:
        best = max(pool, key=lambda f: (len(pool[f] - have), -FALLBACK_CANDIDATES.index(f)))
        gain = len(pool[best] - have)
        if gain == 0:
            break
        choice.fallbacks.append((best, gain))
        have |= pool.pop(best)
    return choice
