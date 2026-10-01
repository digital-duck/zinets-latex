"""Operators, position labels and patterns (see docs/DEV/claude/zi-matrix.md).

The 11 Zi-Matrix labels are canonical in data and code. The Chinese names are accepted as input aliases.
A *pattern* is the labels of a level's immediate components, in order: ``L-M``, ``U-LD-RD``.
"""
from __future__ import annotations

# Canonical position labels
POSITIONS = ("L", "R", "M", "U", "D", "Mi", "Mo", "LU", "LD", "RU", "RD")

# Chinese names, accepted on input and shown as display aliases
ZH = {"L": "左", "R": "右", "M": "中", "U": "上", "D": "下", "Mi": "中内", "Mo": "中外",
      "LU": "左上", "LD": "左下", "RU": "右上", "RD": "右下"}
ALIASES = {zh: code for code, zh in ZH.items()}


def normalize_pos(label: str | None) -> str | None:
    """A Chinese label becomes its code. Anything else is returned unchanged (the validator flags it)."""
    return ALIASES.get(label, label) if label else label


def pattern_of(labels) -> str:
    return "-".join(labels)


def split_pattern(pattern: str) -> tuple[str, ...]:
    return tuple(pattern.split("-"))


# operator -> allowed patterns. The first one is the default when a shape string gives no positions
# (for ⿰ and ⿱ the default is chosen by the radical rule instead, see default_pattern).
_P = split_pattern
OPS: dict[str, tuple[tuple[str, ...], ...]] = {
    "⿰": (_P("L-M"), _P("M-R"), _P("L-R")),
    "⿱": (_P("U-M"), _P("M-D"), _P("U-D")),
    "⿲": (_P("L-M-R"),),
    "⿳": (_P("U-M-D"),),
    "⿴": (_P("Mo-M"),),
    "⿵": (_P("Mo-D"),),
    "⿶": (_P("Mo-U"),),
    "⿷": (_P("Mo-R"),),
    "⿸": (_P("LU-M"),),
    "⿹": (_P("RU-M"),),   # no data in the paper
    "⿺": (_P("LD-M"),),
    "⿻": (_P("M-M"),),    # not defined in the paper
    # ZiNets operators for flat patterns IDS cannot name in one step
    "∴": (_P("U-LD-RD"), _P("U-L-R")),   # apex up; U-L-R is an alias of the same topology
    "∵": (_P("LU-RU-D"),),               # apex down
    "∷": (_P("LU-RU-LD-RD"),),           # 2x2 grid
    "⁙": (_P("LU-RU-M-LD-RD"),),         # four corners and a center
}
FLAT_OPS = frozenset("∴∵∷⁙")
GENERAL_OPEN, GENERAL_CLOSE = "<", ">"   # general form: <L-RU-RD>


def is_general(op: str) -> bool:
    return op.startswith(GENERAL_OPEN) and op.endswith(GENERAL_CLOSE) and len(op) > 2


def general_pattern(op: str) -> tuple[str, ...]:
    return split_pattern(op[1:-1])


def known_op(op: str | None) -> bool:
    return bool(op) and (op in OPS or is_general(op))


def allowed(op: str) -> tuple[tuple[str, ...], ...]:
    """Allowed patterns of an operator. A general <pattern> operator allows exactly itself."""
    return (general_pattern(op),) if is_general(op) else OPS[op]


def arity(op: str) -> int:
    return len(allowed(op)[0])


def default_pattern(op: str, parts) -> tuple[str, ...]:
    """Positions for the children of `op` when a shape string gives none.

    For ⿰ and ⿱ the radical rule applies: a Kangxi radical is peripheral and the other part is M;
    with two radicals or none the parts are peers (L-R, U-D). Everything else uses the first allowed pattern.
    """
    if op in ("⿰", "⿱") and len(parts) == 2:
        from .radicals import is_radical   # local import: radicals is optional data
        first, second = ("L", "R") if op == "⿰" else ("U", "D")
        ra = bool(parts[0].is_leaf and parts[0].c and is_radical(parts[0].c))
        rb = bool(parts[1].is_leaf and parts[1].c and is_radical(parts[1].c))
        if ra and not rb:
            return (first, "M")
        if rb and not ra:
            return ("M", second)
        return (first, second)
    return allowed(op)[0]
