"""Position/structure validator. Everything here is a warning, never a hard failure.

W1  unknown position label
W2  the level's pattern is not allowed for its operator
W3  a non-root component has no position
W4  `shape` does not match the tree
W5  wrong number of children for the operator (or unknown operator)
W6  a branch has no children
W7  position regions overlap, or more than one M (e.g. U-L-R; use U-LD-RD)
W8  a Kangxi radical is labelled M although the other part is not a radical
W9  a reading assigns a role to a component that is not in the tree
W10 a reading uses an unknown role (known: semantic, phonetic, force)
W11 two readings of one character have the same name
"""
from __future__ import annotations

from dataclasses import dataclass

from .loader import ROLES, Entry, role_kinds
from .ops import POSITIONS, allowed, arity, is_general, known_op
from .radicals import is_radical
from .tree import Node, ParseError, leaves, parse_shape, to_shape

# cells of a 3x3 grid (row, col) that a peripheral label claims; M is "whatever is left"
_CORNER = {"LU": (0, 0), "RU": (0, 2), "LD": (2, 0), "RD": (2, 2)}


def _cells(label: str, present: set[str]) -> set[tuple[int, int]]:
    """Cells a label claims. U, D, L and R take a whole row or column, unless something else shares that edge:
    a corner label (LU-U-RU is three parts across the top), or, for L and R, an M or both U and D (U-L-M-D has
    the left part beside M). Then they mean the middle cell of the edge. U-L-R alone stays an overlap."""
    middle_row = "M" in present or {"U", "D"} <= present
    if label in _CORNER:
        return {_CORNER[label]}
    if label == "U":
        return {(0, 1)} if present & {"LU", "RU"} else {(0, 0), (0, 1), (0, 2)}
    if label == "D":
        return {(2, 1)} if present & {"LD", "RD"} else {(2, 0), (2, 1), (2, 2)}
    if label == "L":
        return {(1, 0)} if present & {"LU", "LD"} or middle_row else {(0, 0), (1, 0), (2, 0)}
    if label == "R":
        return {(1, 2)} if present & {"RU", "RD"} or middle_row else {(0, 2), (1, 2), (2, 2)}
    return set()


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
    _readings(e, out)
    if e.shape:
        gen = to_shape(e.tree)
        if gen != e.shape:
            out.append(Warn("W4", e.char, f"shape {e.shape!r} does not match tree {gen!r}"))
        else:
            # the shape should also parse back to the same structure
            try:
                if to_shape(parse_shape(e.shape)) != gen:
                    out.append(Warn("W4", e.char, "shape does not round-trip"))
            except ParseError as ex:
                out.append(Warn("W4", e.char, f"shape does not parse: {ex}"))
    return out


def _readings(e: Entry, out: list[Warn]) -> None:
    parts = {l.c for l in leaves(e.tree) if l.c} | {n.c for n in _named(e.tree)}
    seen: set[str] = set()
    for r in e.readings:
        if r.name in seen:
            out.append(Warn("W11", e.char, f"two readings are named {r.name!r}"))
        seen.add(r.name)
        for comp, value in r.role.items():
            if comp not in parts:
                out.append(Warn("W9", e.char, f"reading {r.name!r}: {comp!r} is not a component of the tree"))
            for kind in role_kinds(value):
                if kind not in ROLES:
                    out.append(Warn("W10", e.char, f"reading {r.name!r}: unknown role {kind!r} for {comp!r}"))


def _named(n: Node):
    if not n.is_leaf:
        if n.c:
            yield n
        for p in n.parts:
            yield from _named(p)


def _walk(n: Node, char: str, out: list[Warn], root: bool) -> None:
    label = n.c or n.op or "?"
    if not root:
        if not n.pos:
            out.append(Warn("W3", char, f"{label!r} has no pos"))
        elif n.pos not in POSITIONS:
            out.append(Warn("W1", char, f"{label!r} has unknown pos {n.pos!r}"))
    if n.is_leaf:
        return
    if not known_op(n.op):
        out.append(Warn("W5", char, f"unknown operator {n.op!r}"))
    else:
        if len(n.parts) != arity(n.op):
            out.append(Warn("W5", char, f"{n.op} needs {arity(n.op)} children, has {len(n.parts)}"))
        else:
            _check_level(n, char, out)
    if not n.parts:
        out.append(Warn("W6", char, f"{n.op} has an empty child list"))
    for p in n.parts:
        _walk(p, char, out, root=False)


def _check_level(n: Node, char: str, out: list[Warn]) -> None:
    labels = tuple(p.pos or "?" for p in n.parts)
    if any(x not in POSITIONS for x in labels):
        return                                   # W1/W3 already reported
    name = n.c or n.op
    if labels not in allowed(n.op):
        out.append(Warn("W2", char, f"{name}: pattern {n.pattern} is not allowed for {n.op} "
                                    f"(allowed: {', '.join('-'.join(a) for a in allowed(n.op))})"))
    if n.op != "⿻" and "Mo" not in labels and "Mi" not in labels:
        _regions(n, labels, char, out)
    if n.op in ("⿰", "⿱") and len(n.parts) == 2:
        a, b = n.parts
        for x, y in ((a, b), (b, a)):
            if (x.pos == "M" and x.is_leaf and x.c and is_radical(x.c)
                    and not (y.is_leaf and y.c and is_radical(y.c))):
                out.append(Warn("W8", char, f"{x.c!r} is a radical but is labelled M "
                                            f"(radicals are peripheral; {y.c or y.op!r} would be M)"))


def _regions(n: Node, labels: tuple[str, ...], char: str, out: list[Warn]) -> None:
    if labels.count("M") > 1:
        out.append(Warn("W7", char, f"{n.pattern} has more than one M"))
    claimed: dict[tuple[int, int], str] = {}
    clash = []
    present = set(labels)
    for lab in labels:
        for cell in _cells(lab, present):
            if cell in claimed and claimed[cell] != lab:
                clash.append(f"{claimed[cell]}/{lab}")
            claimed.setdefault(cell, lab)
    if clash:
        hint = " (use U-LD-RD)" if n.pattern == "U-L-R" else ""
        out.append(Warn("W7", char, f"{n.pattern}: regions overlap ({', '.join(sorted(set(clash)))}){hint}"))
