"""Load character entries from YAML."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .tree import Node, ParseError, node_from_dict, parse_shape


ROLES = ("semantic", "phonetic", "force")


def role_kinds(value) -> list[str]:
    """A role value is one kind or a list of kinds (a component can be both semantic and phonetic)."""
    if not value:
        return []
    return [value] if isinstance(value, str) else [str(v) for v in value]


@dataclass
class Reading:
    """One interpretation of how the components of a character work (e.g. the dictionary's, the author's)."""
    name: str
    role: dict[str, str | list[str]] = field(default_factory=dict)
    note: str | None = None
    source: str | None = None


@dataclass
class Entry:
    char: str
    tree: Node
    shape: str | None = None   # compact form: an IDS-style string with the ZiNets extensions
    pinyin: str | None = None
    meaning: str | None = None
    readings: list[Reading] = field(default_factory=list)   # the first one is the default
    note: str | None = None
    decision: str | None = None
    review: str | None = None

    @property
    def role(self) -> dict:
        """Roles of the default reading."""
        return self.roles_for(None)

    def reading(self, name: str | None):
        if name is None:
            return self.readings[0] if self.readings else None
        return next((r for r in self.readings if r.name == name), None)

    def roles_for(self, name: str | None = None) -> dict:
        """Roles under the reading `name`. An entry without that reading falls back to its default,
        so one reading can be requested for a whole file."""
        r = self.reading(name) or self.reading(None)
        return r.role if r else {}


def entry_from_dict(d: dict) -> Entry:
    if "char" not in d:
        raise ParseError(f"entry has no 'char': {d!r}")
    shape = d.get("shape")
    if d.get("tree"):
        tree = node_from_dict(d["tree"])
    elif shape:
        tree = parse_shape(shape)
    else:
        raise ParseError(f"{d['char']}: needs 'tree' or 'shape'")
    readings = []
    if d.get("role"):                                    # shorthand for a single, unnamed reading
        readings.append(Reading("default", dict(d["role"])))
    for i, r in enumerate(d.get("readings") or []):
        if not isinstance(r, dict) or not r.get("name"):
            raise ParseError(f"{d['char']}: reading #{i + 1} needs a 'name'")
        readings.append(Reading(str(r["name"]), dict(r.get("role") or {}), r.get("note"), r.get("source")))
    return Entry(
        char=d["char"], tree=tree, shape=shape, pinyin=d.get("pinyin"),
        meaning=d.get("meaning"), readings=readings, note=d.get("note"),
        decision=d.get("decision"), review=d.get("review"),
    )


def load_yaml(path: str | Path) -> list[Entry]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        raise ParseError(f"{path}: top level must be a list of entries")
    return [entry_from_dict(d) for d in data]
