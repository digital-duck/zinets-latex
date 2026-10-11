"""Pinyin and per-language glosses for components and characters."""
from __future__ import annotations

import functools
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import config
from .loader import Entry

IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".pdf", ".svg")
EMOJI_FONT_PATHS = ("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
                    "/usr/share/fonts/noto/NotoColorEmoji.ttf", "/System/Library/Fonts/Apple Color Emoji.ttc")


@functools.cache
def _fc_emoji_font() -> str:
    if not shutil.which("fc-match"):
        return ""
    r = subprocess.run(["fc-match", "-f", "%{file}", "Noto Color Emoji"], capture_output=True, text=True)
    return r.stdout.strip()


def emoji_font() -> str | None:
    """Colour emoji font file, or None. XeLaTeX cannot print colour emoji, so an emoji pict is drawn to a picture.
    A font named by ZITEX_EMOJI_FONT is used whatever its file name; the others must have "emoji" in the name
    (fc-match can answer with an unrelated fallback font)."""
    own = config.get("ZITEX_EMOJI_FONT")
    if own and Path(own).is_file():
        return own
    cands = [*EMOJI_FONT_PATHS, _fc_emoji_font()]
    return next((c for c in cands if c and Path(c).is_file() and "emoji" in Path(c).name.lower()), None)


def emoji_available() -> bool:
    """True when an emoji pict can be drawn: Pillow imports and a colour emoji font is found. Both are needed, so the
    renderer never names a picture that staging cannot make (XeLaTeX would stop on the missing file)."""
    try:
        import PIL  # noqa: F401
    except ImportError:
        return False
    return emoji_font() is not None


def emoji_to_png(text: str, dest: Path) -> bool:
    """Draw an emoji (colour) into a trimmed PNG with Pillow. False when Pillow or a font is missing."""
    font = emoji_font()
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return False
    if not font:
        return False
    f = ImageFont.truetype(font, 109)                  # the one size a bitmap emoji font offers
    im = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((20, 20), text, font=f, embedded_color=True)
    box = im.getbbox()
    if not box:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.crop(box).save(dest)
    return True


@dataclass
class Lexicon:
    pinyin: dict[str, str] = field(default_factory=dict)
    gloss: dict[str, dict[str, str]] = field(default_factory=dict)  # char -> lang -> text
    concept: dict[str, str] = field(default_factory=dict)            # char -> ALL-CAPS concept(s), '|'-separated
    category: dict[str, str] = field(default_factory=dict)           # char -> ALL-CAPS concept category
    pict: dict[str, str] = field(default_factory=dict)               # char -> picture file or emoji
    pict_base: dict[str, Path] = field(default_factory=dict)         # char -> folder a relative pict file is in
    sets: dict[str, dict[str, str]] = field(default_factory=dict)    # named pict sets: set -> char -> picture or emoji
    problems: set[str] = field(default_factory=set)                  # pictures asked for that cannot be made (reported)
    set_base: dict[tuple[str, str], Path] = field(default_factory=dict)  # (set, char) -> folder of a relative file
    pict_dir: Path | None = field(default_factory=config.pict_dir)   # u<hex>.png etc. are looked up here

    def get_pinyin(self, ch: str) -> str | None:
        return self.pinyin.get(ch)

    def get_gloss(self, ch: str, lang: str = "en") -> str | None:
        """Gloss in `lang`, falling back to English, then to any language."""
        g = self.gloss.get(ch)
        if not g:
            return None
        if lang in g:
            return g[lang]
        if "en" in g:
            return g["en"]
        return next(iter(g.values()))

    def get_meaning(self, ch: str, lang: str = "en") -> str | None:
        """What to print under a character: its gloss (a concrete phrase), else its concept, else its
        concept category, else nothing (a rare character)."""
        return self.get_gloss(ch, lang) or self.concept.get(ch) or self.category.get(ch) or None

    def _values(self, set: str | None) -> dict[str, str]:
        return self.sets.get(set, {}) if set else self.pict

    def _image(self, ch: str, set: str | None = None) -> Path | None:
        v = self._values(set).get(ch)
        folder = self.pict_dir / set if (set and self.pict_dir) else self.pict_dir
        if v and Path(v).suffix.lower() in IMAGE_SUFFIXES:
            base = self.set_base.get((set, ch)) if set else self.pict_base.get(ch)
            for b in (base, folder, Path(".")):
                if b is not None and (Path(b) / v).is_file():
                    return Path(b) / v
        if folder:
            for suf in IMAGE_SUFFIXES:
                if (folder / f"u{ord(ch):x}{suf}").is_file():
                    return folder / f"u{ord(ch):x}{suf}"
        return None

    def get_pict(self, ch: str, set: str | None = None) -> tuple[str, str] | None:
        """The picture for a character as (kind, value): a small image file, else an emoji, else None.
        ``set`` names an alternative set of pictures (lexicon key ``pict_<set>``, folder ``<pict dir>/<set>``): the
        default set is used when it is None. An emoji only counts when it can be drawn (Pillow and a colour emoji font)."""
        if img := self._image(ch, set):
            return "image", str(img)
        v = self._values(set).get(ch)
        where = f"{ch}" + (f" (set {set})" if set else "")
        if not v:
            return None
        if Path(v).suffix.lower() in IMAGE_SUFFIXES:
            self.problems.add(f"{where}: file not found: {v}")
        elif v.isascii():                       # a word or a path, not an emoji: it would be drawn as nothing
            self.problems.add(f"{where}: {v!r} is neither an image file nor an emoji")
        elif not emoji_available():
            self.problems.add(f"{where}: emoji {v} cannot be drawn (needs Pillow and a colour emoji font)")
        else:
            return "emoji", v
        return None

    def pict_name(self, ch: str, set: str | None = None) -> str | None:
        """File name of the picture inside ``<out>/picts`` (``u4eba.png``, ``u4eba-obs.png`` for the set obs), or None.
        Pure: nothing is written."""
        p = self.get_pict(ch, set)
        if p is None:
            return None
        suffix = Path(p[1]).suffix.lower() if p[0] == "image" else ".png"
        return f"u{ord(ch):x}" + (f"-{set}" if set else "") + (
            ".pdf" if suffix == ".svg" else ".jpg" if suffix == ".jpeg" else suffix)

    def stage_picts(self, chars, outdir: str | Path, set: str | None = None) -> list[str]:
        """Copy (or draw) the pictures ``pict_name`` promised into ``<outdir>/picts``. Returns names written."""
        done = []
        for ch in dict.fromkeys(chars):
            name, p = self.pict_name(ch, set), self.get_pict(ch, set)
            if not name or not p:
                continue
            dest = Path(outdir) / "picts" / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if p[0] == "emoji":
                ok = emoji_to_png(p[1], dest)
            elif Path(p[1]).suffix.lower() == ".svg":
                from .fonts import svg_to_pdf
                svg_to_pdf(Path(p[1]), dest)
                ok = True
            else:
                if not (dest.exists() and dest.samefile(p[1])):   # the picture may already live in <outdir>/picts
                    shutil.copyfile(p[1], dest)
                ok = True
            if ok:
                done.append(name)
            else:
                self.problems.add(f"{ch}: could not draw {p[1]!r} (emoji)")
        return done

    @classmethod
    def from_entries(cls, entries: list[Entry]) -> "Lexicon":
        """Pinyin and the English meaning that characters already carry in chars.yaml."""
        lex = cls()
        for e in entries:
            if e.pinyin:
                lex.pinyin[e.char] = e.pinyin
            if e.meaning:
                lex.gloss.setdefault(e.char, {})["en"] = e.meaning
        return lex

    def merge_file(self, path: str | Path) -> "Lexicon":
        """Add a lexicon YAML; its values override what is already known."""
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        for ch, v in data.items():
            if not isinstance(v, dict):         # an empty entry (`日:`) has nothing to add
                continue
            if v.get("pinyin"):
                self.pinyin[ch] = v["pinyin"]
            for lang, text in (v.get("gloss") or {}).items():
                self.gloss.setdefault(ch, {})[lang] = text
            for key, store in (("concept", self.concept), ("category", self.category)):
                if v.get(key):
                    store[ch] = str(v[key])
            if v.get("pict"):                      # a picture file (relative to this file) or an emoji
                self.pict[ch] = str(v["pict"])
                self.pict_base[ch] = Path(path).resolve().parent
            for key, val in v.items():             # pict_<set>: the same, for a named set of pictures
                if key.startswith("pict_") and len(key) > 5 and val:
                    if "-" in key[5:]:             # file names are style-set-lang: a hyphen would be ambiguous
                        raise ValueError(f"{path}: picture set name {key[5:]!r} must not contain '-'")
                    self.sets.setdefault(key[5:], {})[ch] = str(val)
                    self.set_base[(key[5:], ch)] = Path(path).resolve().parent
        return self


def load_lexicon(entries: list[Entry], *files: str | Path) -> Lexicon:
    lex = Lexicon.from_entries(entries)
    for f in files:
        lex.merge_file(f)
    return lex
