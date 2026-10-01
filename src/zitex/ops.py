"""Operator table: arity and default child positions (see docs/DEV/claude/spec.md)."""

# The 11 position labels from the paper.
POSITIONS = ("上", "下", "左", "右", "中", "左上", "右上", "左下", "右下", "中内", "中外")

# op -> default position of each child, in order. Arity is len(positions).
OPS: dict[str, tuple[str, ...]] = {
    "⿰": ("左", "右"),
    "⿱": ("上", "下"),
    "⿲": ("左", "中", "右"),
    "⿳": ("上", "中", "下"),
    "⿴": ("中外", "中内"),
    "⿵": ("中外", "中内"),
    "⿶": ("中外", "中内"),
    "⿷": ("中外", "中内"),
    "⿸": ("左上", "中内"),
    "⿹": ("右上", "中内"),
    "⿺": ("左下", "中内"),
    "⿻": ("中", "中"),
    "∴": ("上", "左下", "右下"),  # ZiNets: apex up
    "∵": ("左上", "右上", "下"),  # ZiNets: apex down
}


def arity(op: str) -> int:
    return len(OPS[op])
