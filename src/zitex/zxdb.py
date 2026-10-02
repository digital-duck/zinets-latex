"""zitex's own small database tables (zx_*), derived from the ZiNets working database.

The working database (t_zi_part, t_zi, t_ele_zi, t_part, ...) is the author's, it is still being reviewed, and
zitex never changes it. This module does two separate things:

  build_from_raw()  reads the working tables READ ONLY and re-creates just the data zitex needs, in a clean shape
  write_zx()        writes that into four tables, in a *separate* SQLite file by default

    zx_meta        where and when the copy was made (source file, size, SHA-256, counts)
    zx_char        one row per character: pinyin, English gloss, meaning, is_elemental, is_root, has_parts
    zx_part        one row per component, in reading order: (zi, ord, pos, part)
    zx_quarantine  working-table rows that could not be converted safely, with the reason

Because the copy is derived, it can be thrown away and rebuilt at any time.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import pinyin
from .ops import pattern_of, reading_order

ZX_TABLES = ("zx_meta", "zx_char", "zx_part", "zx_quarantine")

# The dictionary definitions in the working database (t_zi.desc_en, and the pinyin of t_zi) are CEDICT entries.
# CC-CEDICT is licensed CC BY-SA, which asks for attribution, a note of the changes, and the same licence for
# adaptations. The text travels with the data: it is stored in zx_meta and written into exported YAML files.
ATTRIBUTION = (
    "English glosses and meanings, and the pinyin of characters that are not in the elemental set, are derived from "
    "CC-CEDICT (https://cc-cedict.org), licensed CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/). "
    "Changes: tone numbers converted to tone marks; each definition shortened to its first sense (at most three senses "
    "for the meaning), with cross-references and notes removed."
)

SCHEMA = """
CREATE TABLE zx_meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE zx_char (
    zi TEXT PRIMARY KEY,
    pinyin TEXT,
    gloss_en TEXT,
    meaning TEXT,
    is_elemental INTEGER NOT NULL DEFAULT 0,
    is_root INTEGER NOT NULL DEFAULT 0,
    has_parts INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE zx_part (
    zi TEXT NOT NULL,
    ord INTEGER NOT NULL,
    pos TEXT NOT NULL,
    part TEXT NOT NULL,
    PRIMARY KEY (zi, ord)
);
CREATE INDEX zx_part_part ON zx_part (part);
CREATE TABLE zx_quarantine (zi TEXT PRIMARY KEY, reason TEXT NOT NULL, cells TEXT);
"""

# t_zi_part: one row per character, one column per position (an empty cell means "no part there")
COLUMNS = {"zi_left_up": "LU", "zi_left": "L", "zi_left_down": "LD", "zi_up": "U", "zi_mid": "M", "zi_down": "D",
           "zi_right_up": "RU", "zi_right": "R", "zi_right_down": "RD", "zi_mid_out": "Mo", "zi_mid_in": "Mi"}


@dataclass
class ZxChar:
    pinyin: str | None = None
    gloss_en: str | None = None
    meaning: str | None = None
    is_elemental: bool = False
    is_root: bool = False
    has_parts: bool = False


@dataclass
class ZxData:
    chars: dict[str, ZxChar] = field(default_factory=dict)
    parts: dict[str, list[tuple[str, str]]] = field(default_factory=dict)       # zi -> [(pos, part)] in reading order
    quarantine: list[tuple[str, str, str]] = field(default_factory=list)       # (zi, reason, cells as text)
    meta: dict[str, str] = field(default_factory=dict)


# ---- small text helpers ------------------------------------------------------------------------------

def _senses(desc: str | None) -> list[str]:
    """The senses of a CEDICT-style definition, without its cross-references ("CL:臺|台[tai2]", "used in 舾裝|舾装[xi1 zhuang1]")."""
    out = []
    for s in re.split(r"[;/]", desc or ""):
        s = s.strip()
        if not s or "|" in s or "[" in s or s.startswith("CL:"):
            continue
        cleaned = re.sub(r"\s*\([^)]*\)\s*", " ", s).strip()      # drop "(bound form)" and the like
        out.append(cleaned or s)
    return out


def short_gloss(desc: str | None) -> str | None:
    """A short English gloss from a CEDICT-style definition ("(bound form) up; upper" -> "up")."""
    senses = _senses(desc)
    return senses[0] if senses else None


def meaning_text(desc: str | None, n: int = 3) -> str | None:
    """The first few senses, joined with "; "."""
    senses = _senses(desc)
    return "; ".join(senses[:n]) if senses else None


def sha256_of(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _connect_ro(path: str | Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro", uri=True)


def _tables(con: sqlite3.Connection) -> set[str]:
    return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def has_zx(path: str | Path) -> bool:
    con = _connect_ro(path)
    try:
        return set(ZX_TABLES) <= _tables(con)
    finally:
        con.close()


def has_raw(path: str | Path) -> bool:
    con = _connect_ro(path)
    try:
        return {"t_zi_part", "t_zi"} <= _tables(con)
    finally:
        con.close()


# ---- the working tables -> clean data (READ ONLY) -----------------------------------------------------

def build_from_raw(path: str | Path) -> ZxData:
    """Re-create the data zitex needs from the working tables. The file is opened read only."""
    zx = ZxData()
    con = _connect_ro(path)
    try:
        cur = con.cursor()
        raw: dict[str, tuple[bool, dict[str, str]]] = {}
        cols = ", ".join(COLUMNS)
        for zi, active, *cells in cur.execute(f"SELECT zi, is_active, {cols} FROM t_zi_part"):
            raw[zi] = (active == "Y", {lab: v for lab, v in zip(COLUMNS.values(), cells) if v is not None and v != ""})
        zi_tab = {r[0]: (r[1], r[2]) for r in cur.execute("SELECT zi, pinyin, desc_en FROM t_zi")}
        ele = {r[0]: (r[1], r[2]) for r in cur.execute("SELECT zi, meaning, pinyin FROM t_ele_zi WHERE is_active = 'Y'")}
        part_tab = {r[0]: (r[1], r[2]) for r in cur.execute("SELECT zi, meaning, pinyin FROM t_part")}
    finally:
        con.close()

    # decide which rows can be converted safely; the others are listed, not guessed at
    roots: set[str] = set()
    for zi, (active, cells) in raw.items():
        shown = " ".join(f"{k}={v}" for k, v in cells.items())
        if not active:
            zx.quarantine.append((zi, "row is not active", shown))
        elif not cells:
            roots.add(zi)                                              # a primitive: no decomposition
        elif any(len(v) != 1 for v in cells.values()):
            zx.quarantine.append((zi, "a position holds more than one part", shown))
        elif "?" in cells.values():
            zx.quarantine.append((zi, "a part is the placeholder ?", shown))
        elif len(cells) == 1:
            zx.quarantine.append((zi, "only one part (incomplete)", shown))
        else:
            roots.add(zi)
            order = reading_order(cells)
            zx.parts[zi] = [(label, cells[label]) for label in order]

    used = set(roots) | {p for lst in zx.parts.values() for _, p in lst}
    for ch in sorted(used):
        item = ZxChar(is_elemental=ch in ele, is_root=ch in roots, has_parts=ch in zx.parts)
        pin = gloss = None
        # an elemental character or a radical has a curated one-word meaning, so it comes first;
        # every other character falls back on the dictionary entry (t_zi)
        for src in (ele.get(ch), part_tab.get(ch)):
            if src and not gloss and src[0]:
                gloss = src[0].split("/")[0].strip()
            if src and not pin and src[1]:
                pin = pinyin.first_reading(src[1])
        zrow = zi_tab.get(ch)
        if zrow:
            pin = pin or pinyin.first_reading(zrow[0])
            gloss = gloss or short_gloss(zrow[1])
            if ch in roots:
                item.meaning = meaning_text(zrow[1])
        item.pinyin, item.gloss_en = pin, gloss
        zx.chars[ch] = item

    zx.meta = {
        "source": Path(path).name,                    # the name only: an absolute path would travel with the file
        "source_size": str(Path(path).stat().st_size),
        "source_sha256": sha256_of(path),
        "raw_rows": str(len(raw)),
        "roots": str(len(roots)),
        "with_parts": str(len(zx.parts)),
        "quarantined": str(len(zx.quarantine)),
        "attribution": ATTRIBUTION,
    }
    return zx


# ---- zx tables: write and read -------------------------------------------------------------------------

def write_zx(zx: ZxData, out: str | Path, source: str | Path | None = None, in_place: bool = False) -> Path:
    """Write the zx tables into `out`, replacing earlier zx tables there.

    A file that already holds other tables is refused unless `in_place` is true. That is the case of
    writing into the working database itself: a dated backup copy is made first. The default is a separate file.
    """
    out = Path(out)
    if out.exists():
        con = _connect_ro(out)
        try:
            foreign = _tables(con) - set(ZX_TABLES)
        finally:
            con.close()
        if foreign and not in_place:
            raise ValueError(f"{out} holds other tables ({', '.join(sorted(foreign)[:4])}, ...): "
                             "not writing into it. Use a separate file, or --in-place to add the zx tables to it "
                             "(a backup copy is made first).")
        if foreign and in_place:
            backup = out.with_name(f"{out.name}.bak-{time.strftime('%Y%m%d-%H%M%S')}")
            shutil.copy2(out, backup)
    con = sqlite3.connect(out)
    try:
        with con:
            for t in ZX_TABLES:
                con.execute(f"DROP TABLE IF EXISTS {t}")
            con.executescript(SCHEMA)
            con.executemany(
                "INSERT INTO zx_char (zi, pinyin, gloss_en, meaning, is_elemental, is_root, has_parts) VALUES (?,?,?,?,?,?,?)",
                [(zi, c.pinyin, c.gloss_en, c.meaning, int(c.is_elemental), int(c.is_root), int(c.has_parts))
                 for zi, c in sorted(zx.chars.items())])
            con.executemany("INSERT INTO zx_part (zi, ord, pos, part) VALUES (?,?,?,?)",
                            [(zi, i, pos, part) for zi, lst in sorted(zx.parts.items()) for i, (pos, part) in enumerate(lst)])
            con.executemany("INSERT INTO zx_quarantine (zi, reason, cells) VALUES (?,?,?)", zx.quarantine)
            from . import __version__
            meta = {**zx.meta, "built_at": time.strftime("%Y-%m-%d %H:%M:%S"), "zitex_version": __version__}
            con.executemany("INSERT INTO zx_meta (key, value) VALUES (?,?)", sorted(meta.items()))
    finally:
        con.close()
    return out


def read_zx(path: str | Path) -> ZxData:
    con = _connect_ro(path)
    try:
        zx = ZxData()
        for zi, py, gl, mean, ele, root, has in con.execute(
                "SELECT zi, pinyin, gloss_en, meaning, is_elemental, is_root, has_parts FROM zx_char"):
            zx.chars[zi] = ZxChar(py, gl, mean, bool(ele), bool(root), bool(has))
        for zi, pos, part in con.execute("SELECT zi, pos, part FROM zx_part ORDER BY zi, ord"):
            zx.parts.setdefault(zi, []).append((pos, part))
        zx.quarantine = [tuple(r) for r in con.execute("SELECT zi, reason, cells FROM zx_quarantine ORDER BY zi")]
        zx.meta = dict(con.execute("SELECT key, value FROM zx_meta"))
        return zx
    finally:
        con.close()
