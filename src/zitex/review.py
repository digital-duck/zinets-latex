"""What the review page of the Streamlit app needs: the problems in a zx database, and a safe way to try a revision.

Nothing here writes to a database except through zxdb.revise() and zxdb.revert(), and only to a zx file.
"""
from __future__ import annotations

import csv
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from . import zxdb
from .loader import Entry
from .sources import SqliteSource
from .validate import Warn, validate_entry

KINDS = {
    "quarantine": "Left out of the database (cannot be converted yet)",
    "elemental": "Elemental characters that still have a decomposition",
    "mi": "Patterns that use Mi (to review)",
    "w8": "A radical is labelled M (W8)",
    "w7": "Position regions overlap (W7)",
    "revised": "Revised by hand",
}


@dataclass
class ReviewData:
    entries: dict[str, Entry] = field(default_factory=dict)
    warnings: dict[str, list[Warn]] = field(default_factory=dict)
    quarantine: list[tuple[str, str, str]] = field(default_factory=list)
    revisions: list[dict] = field(default_factory=list)
    elemental_decomposed: list[tuple[str, str]] = field(default_factory=list)      # (zi, "L=乀 R=韋")
    used_in: dict[str, list[str]] = field(default_factory=dict)                    # part -> characters that use it
    elemental: set[str] = field(default_factory=set)                              # characters flagged elemental
    from_raw: bool = False
    meta: dict[str, str] = field(default_factory=dict)

    @property
    def counts(self) -> dict[str, int]:
        return {"characters": len(self.entries), "with warnings": len(self.warnings), "left out": len(self.quarantine),
                "elemental, decomposed": len(self.elemental_decomposed), "revised": len(self.revisions)}


def load_review(path: str | Path) -> ReviewData:
    src = SqliteSource(path)
    entries = {e.char: e for e in src.entries()}
    data = ReviewData(entries=entries, from_raw=src.from_raw, meta=dict(src.report.meta))
    for e in entries.values():
        ws = validate_entry(e)
        if ws:
            data.warnings[e.char] = ws
    zx = src.zx
    data.quarantine = list(zx.quarantine)
    data.elemental = {zi for zi, c in zx.chars.items() if c.is_elemental}
    data.elemental_decomposed = [(zi, " ".join(f"{p}={c}" for p, c in zx.parts[zi])) for zi, c in sorted(zx.chars.items())
                                 if c.is_elemental and c.has_parts]
    for zi, parts in zx.parts.items():
        for _, part in parts:
            data.used_in.setdefault(part, []).append(zi)
    if not src.from_raw:
        data.revisions = zxdb.list_revisions(path)
    return data


def issue_rows(data: ReviewData, kind: str) -> list[dict]:
    """Rows for a table of one kind of problem. Every row has a "char" to open."""
    def row(zi, **extra):
        e = data.entries.get(zi)
        return {"char": zi, "pinyin": e.pinyin if e else "", "shape": e.shape if e else "", **extra}
    if kind == "quarantine":
        return [row(zi, reason=reason, cells=cells) for zi, reason, cells in data.quarantine]
    if kind == "elemental":
        return [row(zi, decomposition=parts) for zi, parts in data.elemental_decomposed]
    if kind == "mi":
        return [row(zi, note=e.review) for zi, e in data.entries.items() if e.review]
    if kind in ("w7", "w8"):
        code = kind.upper()
        return [row(zi, warning="; ".join(w.msg for w in ws if w.code == code)) for zi, ws in data.warnings.items()
                if any(w.code == code for w in ws)]
    if kind == "revised":
        return [row(r["zi"], parts=" ".join(f"{p}={c}" for p, c in r["parts"]) or "(a primitive)", note=r.get("note") or "",
                    when=r.get("ts") or "") for r in data.revisions]
    raise KeyError(kind)


@dataclass
class Preview:
    entry: Entry | None
    shape: str = ""
    pattern: str = ""
    warnings: list[Warn] = field(default_factory=list)
    error: str = ""


def preview_revision(path: str | Path, zi: str, parts, elemental: bool | None = None) -> Preview:
    """What `zi` would look like with `parts`, tried on a throw-away copy of the file. The real file is not touched."""
    try:
        zxdb.check_parts(zi, parts)
    except ValueError as ex:
        return Preview(None, error=str(ex))
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "preview.sqlite3"
        shutil.copyfile(path, copy)
        zxdb.revise(copy, zi, parts, elemental=elemental)
        entry = next((e for e in SqliteSource(copy).entries() if e.char == zi), None)
    if entry is None:
        return Preview(None, error=f"{zi} is not an entry after this change")
    return Preview(entry, entry.shape, entry.tree.pattern or "", validate_entry(entry))


def level_of(path: str | Path, zi: str) -> list[tuple[str, str]]:
    """The (position, part) rows stored for `zi`, in reading order."""
    import sqlite3
    con = sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro", uri=True)
    try:
        return [(p, c) for p, c in con.execute("SELECT pos, part FROM zx_part WHERE zi = ? ORDER BY ord", (zi,))]
    finally:
        con.close()


# the four lists of the review page's metrics row, as CSV files: name -> (file, columns)
EXPORTS = {
    "with warnings": "review-with-warnings.csv",
    "left out": "review-left-out.csv",
    "elemental, decomposed": "review-elemental-decomposed.csv",
    "revised": "review-revised.csv",
}


def export_tables(data: ReviewData) -> dict[str, tuple[list[str], list[list[str]]]]:
    """The lists behind the metrics of the review page, each as (header, rows): file name -> table."""
    def entry_cols(zi):
        e = data.entries.get(zi)
        return [e.pinyin or "", e.meaning or "", e.shape] if e else ["", "", ""]
    warned = [[zi, *entry_cols(zi), " ".join(sorted({w.code for w in ws})), "; ".join(f"{w.code} {w.msg}" for w in ws),
               " ".join(f"{n.pos}={n.c}" for n in data.entries[zi].tree.parts if n.c)]
              for zi, ws in sorted(data.warnings.items())]
    return {
        EXPORTS["with warnings"]: (["char", "pinyin", "meaning", "shape", "codes", "warnings", "first_level_parts"], warned),
        EXPORTS["left out"]: (["char", "reason", "cells"], [[zi, reason, cells] for zi, reason, cells in data.quarantine]),
        EXPORTS["elemental, decomposed"]: (["char", "pinyin", "meaning", "shape", "decomposition"],
                                           [[zi, *entry_cols(zi), parts] for zi, parts in data.elemental_decomposed]),
        EXPORTS["revised"]: (["char", "parts", "note", "when"],
                             [[r["zi"], " ".join(f"{p}={c}" for p, c in r["parts"]) or "(a primitive)", r.get("note") or "",
                               r.get("ts") or ""] for r in data.revisions]),
    }


def export_csv(path: str | Path, out_dir: str | Path) -> dict[str, int]:
    """Write the four lists of the review page as CSV files in out_dir (UTF-8 with a BOM, so Excel shows the Chinese).
    Returns file name -> number of rows. The database is only read."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    counts = {}
    for name, (header, rows) in export_tables(load_review(path)).items():
        with open(out / name, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
        counts[name] = len(rows)
    return counts
