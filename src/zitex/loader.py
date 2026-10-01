"""Load character entries from YAML."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .tree import Node, ParseError, node_from_dict, parse_ids


@dataclass
class Entry:
    char: str
    tree: Node
    ids: str | None = None
    pinyin: str | None = None
    meaning: str | None = None
    role: dict[str, str] = field(default_factory=dict)
    note: str | None = None
    decision: str | None = None
    review: str | None = None


def entry_from_dict(d: dict) -> Entry:
    if "char" not in d:
        raise ParseError(f"entry has no 'char': {d!r}")
    if d.get("tree"):
        tree = node_from_dict(d["tree"])
    elif d.get("ids"):
        tree = parse_ids(d["ids"])
    else:
        raise ParseError(f"{d['char']}: needs 'tree' or 'ids'")
    return Entry(
        char=d["char"], tree=tree, ids=d.get("ids"), pinyin=d.get("pinyin"),
        meaning=d.get("meaning"), role=d.get("role") or {}, note=d.get("note"),
        decision=d.get("decision"), review=d.get("review"),
    )


def load_yaml(path: str | Path) -> list[Entry]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        raise ParseError(f"{path}: top level must be a list of entries")
    return [entry_from_dict(d) for d in data]
