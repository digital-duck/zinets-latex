"""Decomposition tree: the Node model, the compact `shape` parser and serializer."""
from __future__ import annotations

from dataclasses import dataclass, field

from .ops import (GENERAL_CLOSE, GENERAL_OPEN, OPS, POSITIONS, arity, default_pattern, general_pattern,
                  normalize_pos, pattern_of)


class ParseError(ValueError):
    pass


@dataclass
class Node:
    """Leaf: c only. Branch: op + parts. Named branch: c + op + parts."""
    c: str | None = None
    op: str | None = None
    pos: str | None = None
    parts: list["Node"] = field(default_factory=list)

    @property
    def is_leaf(self) -> bool:
        return self.op is None

    @property
    def pattern(self) -> str | None:
        """Compositional pattern of this level, e.g. ``L-M``: the labels of the immediate components."""
        return pattern_of(p.pos or "?" for p in self.parts) if self.parts else None


# ---- shape string -> tree ------------------------------------------------------------

def parse_shape(s: str) -> Node:
    """Parse the compact prefix form, e.g. ``⿱艹⿰氵喿(⿱品(∴口口口)木)``.

    Children get the default positions for their operator (for ⿰ and ⿱ chosen by the radical rule,
    see ops.default_pattern). The root has no pos.
    """
    node, i = _expr(s, 0)
    if i != len(s):
        raise ParseError(f"unexpected {s[i]!r} at {i} in {s!r}")
    return node


def _expr(s: str, i: int) -> tuple[Node, int]:
    if i >= len(s):
        raise ParseError(f"unexpected end of input in {s!r}")
    ch = s[i]
    i += 1
    if ch in OPS or ch == GENERAL_OPEN:
        op = ch
        if ch == GENERAL_OPEN:               # general form <L-RU-RD>
            end = s.find(GENERAL_CLOSE, i)
            if end <= i:
                raise ParseError(f"unterminated or empty <pattern> in {s!r}")
            op = GENERAL_OPEN + s[i:end] + GENERAL_CLOSE
            bad = [x for x in general_pattern(op) if x not in POSITIONS]
            if bad:
                raise ParseError(f"unknown position label(s) {bad} in {op!r}")
            i = end + 1
        parts = []
        for _ in range(arity(op)):
            child, i = _expr(s, i)
            parts.append(child)
        for child, pos in zip(parts, default_pattern(op, parts)):
            child.pos = pos
        return Node(op=op, parts=parts), i
    if ch in "()":
        raise ParseError(f"unexpected {ch!r} at {i - 1} in {s!r}")
    if ch == "{":  # a component with no code point, written by name: {name}
        end = s.find("}", i)
        if end <= i:
            raise ParseError(f"unterminated or empty {{name}} in {s!r}")
        ch, i = s[i:end], end + 1
    if i < len(s) and s[i] == "(":
        inner, i = _expr(s, i + 1)
        if i >= len(s) or s[i] != ")":
            raise ParseError(f"missing ')' after name {ch!r} in {s!r}")
        if inner.is_leaf:
            raise ParseError(f"name {ch!r} must label an operator expression, not a leaf")
        inner.c = ch
        return inner, i + 1
    return Node(c=ch), i


# ---- tree -> shape string ------------------------------------------------------------

def to_shape(n: Node) -> str:
    name = _name(n.c)
    if n.is_leaf:
        return name
    body = n.op + "".join(to_shape(p) for p in n.parts)
    return f"{name}({body})" if n.c else body


def _name(c: str | None) -> str:
    """One code point is written as is; a longer component name is written {name}."""
    c = c or ""
    return "{" + c + "}" if len(c) > 1 else c


# ---- dict (YAML) <-> tree ---------------------------------------------------

def node_from_dict(d: dict) -> Node:
    if not isinstance(d, dict):
        raise ParseError(f"tree node must be a mapping, got {d!r}")
    parts = [node_from_dict(p) for p in d.get("parts") or []]
    return Node(c=d.get("c"), op=d.get("op"), pos=normalize_pos(d.get("pos")), parts=parts)


def node_to_dict(n: Node) -> dict:
    d: dict = {}
    if n.c:
        d["c"] = n.c
    if n.op:
        d["op"] = n.op
    if n.pos:
        d["pos"] = n.pos
    if n.parts:
        d["parts"] = [node_to_dict(p) for p in n.parts]
    return d


def leaves(n: Node) -> list[Node]:
    return [n] if n.is_leaf else [l for p in n.parts for l in leaves(p)]


__all__ = ["Node", "ParseError", "parse_shape", "to_shape", "node_from_dict", "node_to_dict", "leaves", "arity"]
