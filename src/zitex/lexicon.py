"""Pinyin and per-language glosses for components and characters."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .loader import Entry


@dataclass
class Lexicon:
    pinyin: dict[str, str] = field(default_factory=dict)
    gloss: dict[str, dict[str, str]] = field(default_factory=dict)  # char -> lang -> text

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
            if v.get("pinyin"):
                self.pinyin[ch] = v["pinyin"]
            for lang, text in (v.get("gloss") or {}).items():
                self.gloss.setdefault(ch, {})[lang] = text
        return self


def load_lexicon(entries: list[Entry], *files: str | Path) -> Lexicon:
    lex = Lexicon.from_entries(entries)
    for f in files:
        lex.merge_file(f)
    return lex
