"""Data adapters: where decompositions and lexicons come from.

Every adapter produces the same two things, entries (decomposition trees) and a lexicon (pinyin and glosses):

  YamlSource    a chars.yaml of entries, plus lexicon YAML files          (the prototype, hand-curated)
  SqliteSource  zitex's own tables (zx_*), derived from the ZiNets database (the 6000-character data)

The SQLite adapter has no renderer or validator of its own. It turns each character into the *same dictionary
that a chars.yaml entry loads from* and passes it through ``entry_from_dict``, so everything after that
(validation, rendering, extraction to YAML) is one code path. ``zitex extract`` writes those dictionaries as YAML,
which is the reviewable intermediate form.

The adapter reads only the zx_* tables (see zxdb.py). Given the raw working database instead, it re-creates them
in memory and writes nothing.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from . import zxdb
from .lexicon import Lexicon, load_lexicon
from .loader import Entry, entry_from_dict, load_yaml
from .ops import pattern_of
from .tree import node_from_dict, to_shape

SQLITE_MAGIC = b"SQLite format 3\x00"
DEFAULT_DEPTH = 12          # a guard against cycles and runaway nesting, far deeper than any real character


class Source(Protocol):
    def entries(self) -> list[Entry]: ...
    def lexicon(self, files=()) -> Lexicon: ...


def is_sqlite(path: str | Path) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(16) == SQLITE_MAGIC
    except OSError:
        return False


def open_source(path: str | Path, depth: int | None = None) -> "YamlSource | SqliteSource":
    """A SQLite file (recognised by its header, whatever its name) or a decomposition YAML."""
    return SqliteSource(path, depth=depth) if is_sqlite(path) else YamlSource(path)


# ---- YAML ------------------------------------------------------------------------------------------

class YamlSource:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._entries: list[Entry] | None = None

    def entries(self) -> list[Entry]:
        if self._entries is None:
            self._entries = load_yaml(self.path)
        return self._entries

    def lexicon(self, files=()) -> Lexicon:
        return load_lexicon(self.entries(), *files)


# ---- SQLite ----------------------------------------------------------------------------------------

@dataclass
class DbReport:
    quarantined: list[tuple[str, str, str]] = field(default_factory=list)   # (zi, reason, cells shown as text)
    no_decomposition: list[str] = field(default_factory=list)
    to_review: list[tuple[str, str]] = field(default_factory=list)          # exported, but worth a look
    patterns: Counter = field(default_factory=Counter)                      # pattern of each decomposed character
    meta: dict[str, str] = field(default_factory=dict)


class SqliteSource:
    """zitex's zx_* tables, or the raw working database (converted in memory)."""

    def __init__(self, path: str | Path, depth: int | None = None):
        self.path = Path(path)
        self.depth = DEFAULT_DEPTH if depth is None else depth
        self.from_raw = False
        self.report = DbReport()
        self._zx: zxdb.ZxData | None = None
        self._dicts: list[dict] | None = None
        self._entries: list[Entry] | None = None

    @property
    def zx(self) -> zxdb.ZxData:
        if self._zx is None:
            if zxdb.has_zx(self.path):
                self._zx = zxdb.read_zx(self.path)
            elif zxdb.has_raw(self.path):
                self.from_raw = True          # nothing is written: the zx data lives in memory only
                self._zx = zxdb.build_from_raw(self.path)
            else:
                raise ValueError(f"{self.path}: neither the zx_* tables nor the working tables (t_zi_part, t_zi) are in it")
            self.report.quarantined = list(self._zx.quarantine)
            self.report.meta = dict(self._zx.meta)
        return self._zx

    def _branch(self, zi: str, path: tuple[str, ...], depth: int, flags: set[str]) -> dict:
        zx = self.zx
        parts = zx.parts[zi]
        pattern = pattern_of(pos for pos, _ in parts)
        if any(pos == "Mi" for pos, _ in parts):
            flags.add(f"{pattern} uses Mi, which is being reviewed")
        from .ops import op_for_pattern
        node: dict = {"op": op_for_pattern([pos for pos, _ in parts]), "parts": []}
        for pos, comp in parts:
            info = zx.chars.get(comp)
            if info and info.has_parts and not info.is_elemental and comp not in path and depth > 1:
                child = {"c": comp, **self._branch(comp, (*path, comp), depth - 1, flags)}
            else:
                child = {"c": comp}
            child["pos"] = pos
            node["parts"].append(child)
        return node

    def entry_dicts(self) -> list[dict]:
        if self._dicts is not None:
            return self._dicts
        zx = self.zx
        out = []
        for zi, info in sorted(zx.chars.items()):
            if not info.is_root:
                continue
            d: dict = {"char": zi}
            if info.pinyin:
                d["pinyin"] = info.pinyin
            if info.meaning:
                d["meaning"] = info.meaning
            if not info.has_parts:
                d["shape"], d["tree"] = zi, {"c": zi}
                d["note"] = "no decomposition in the database"
                self.report.no_decomposition.append(zi)
            else:
                flags: set[str] = set()
                tree = self._branch(zi, (zi,), self.depth, flags)
                d["shape"], d["tree"] = to_shape(node_from_dict(tree)), tree
                self.report.patterns[pattern_of(pos for pos, _ in zx.parts[zi])] += 1
                if flags:
                    d["review"] = "; ".join(sorted(flags))
                    self.report.to_review.append((zi, d["review"]))
            out.append(d)
        self._dicts = out
        return out

    def entries(self) -> list[Entry]:
        if self._entries is None:
            self._entries = [entry_from_dict(d) for d in self.entry_dicts()]    # the same path as a chars.yaml entry
        return self._entries

    def lexicon_dict(self) -> dict[str, dict]:
        """pinyin and an English gloss for every character that appears in an exported entry."""
        used: set[str] = set()

        def collect(node: dict) -> None:
            if "c" in node:
                used.add(node["c"])
            for p in node.get("parts", []):
                collect(p)

        for d in self.entry_dicts():
            collect(d["tree"])
            used.add(d["char"])
        lex: dict[str, dict] = {}
        for ch in sorted(used):
            info = self.zx.chars.get(ch)
            item: dict = {}
            if info and info.pinyin:
                item["pinyin"] = info.pinyin
            if info and info.gloss_en:
                item["gloss"] = {"en": info.gloss_en}
            if item:
                lex[ch] = item
        return lex

    def lexicon(self, files=()) -> Lexicon:
        lex = Lexicon()
        for ch, v in self.lexicon_dict().items():
            if v.get("pinyin"):
                lex.pinyin[ch] = v["pinyin"]
            for lang, text in (v.get("gloss") or {}).items():
                lex.gloss.setdefault(ch, {})[lang] = text
        for f in files:                      # files given by the user replace what the database says
            lex.merge_file(f)
        return lex
