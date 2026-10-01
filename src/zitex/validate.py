"""Position/structure validator. Everything here is a warning, never a hard failure."""
from __future__ import annotations

from dataclasses import dataclass

from .loader import Entry
from .ops import OPS, POSITIONS
from .tree import Node, ParseError, parse_ids, to_ids


@dataclass(frozen=True)
class Warn:
    code: str
    char: str
    msg: str

    def __str__(self) -> str:
        return f"{self.code} {self.char}: {self.msg}"


def validate_entry(e: Entry) -> list[Warn]:
    out: list[Warn] = []
    _walk(e.tree, e.char, out, root=True)
    if e.ids:
        gen = to_ids(e.tree)
        if gen != e.ids:
            out.append(Warn("W4", e.char, f"ids {e.ids!r} does not match tree {gen!r}"))
        else:
            # the compact form should also parse back to the same structure
            try:
                if to_ids(parse_ids(e.ids)) != gen:
                    out.append(Warn("W4", e.char, "ids does not round-trip"))
            except ParseError as ex:
                out.append(Warn("W4", e.char, f"ids does not parse: {ex}"))
    return out


def _walk(n: Node, char: str, out: list[Warn], root: bool, parent: Node | None = None, idx: int = 0) -> None:
    label = n.c or n.op or "?"
    if not root:
        if not n.pos:
            out.append(Warn("W3", char, f"{label!r} has no pos"))
        elif n.pos not in POSITIONS:
            out.append(Warn("W1", char, f"{label!r} has unknown pos {n.pos!r}"))
        elif parent is not None and parent.op in OPS:
            defaults = OPS[parent.op]
            if idx < len(defaults) and n.pos != defaults[idx]:
                out.append(Warn("W2", char, f"{label!r} pos {n.pos!r} differs from {parent.op} default {defaults[idx]!r}"))
    if n.is_leaf:
        return
    if n.op not in OPS:
        out.append(Warn("W5", char, f"unknown operator {n.op!r}"))
    elif len(n.parts) != len(OPS[n.op]):
        out.append(Warn("W5", char, f"{n.op} needs {len(OPS[n.op])} children, has {len(n.parts)}"))
    if not n.parts:
        out.append(Warn("W6", char, f"{n.op} has an empty child list"))
    for i, p in enumerate(n.parts):
        _walk(p, char, out, root=False, parent=n, idx=i)
