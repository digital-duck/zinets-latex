"""The 214 Kangxi radicals, their common variant forms, and lookup helpers.

Used for the Zi-Matrix rule that a Kangxi radical is *peripheral* and the other component of a
two-part character is ``M``, the center of gravity (see docs/DEV/claude/zi-matrix.md).

Three sources:
  * KANGXI: the 214 radicals, generated from Unicode (NFKC of U+2F00..U+2FD5), numbered 1..214.
  * VARIANTS: ideograph-form variants used as components (亻 氵 忄 艹 辶 ...), mapped to their base radical.
    Curated by hand, because Unicode does not link them.
  * the CJK Radicals Supplement block (U+2E80..U+2EF3): radical forms by definition. Where the
    Unicode name matches a Kangxi radical name the base is known, otherwise only membership is.
"""
from __future__ import annotations

import re
import unicodedata

KANGXI: tuple[str, ...] = tuple(unicodedata.normalize("NFKC", chr(cp)) for cp in range(0x2F00, 0x2FD6))

# variant -> base Kangxi radical (a character in KANGXI). Hand-curated; extend as needed.
VARIANTS: dict[str, str] = {
    "亻": "人", "𠆢": "人",
    "氵": "水", "氺": "水",
    "忄": "心", "㣺": "心",
    "扌": "手", "犭": "犬", "艹": "艸", "辶": "辵", "刂": "刀",
    "礻": "示", "衤": "衣", "灬": "火", "爫": "爪", "牜": "牛",
    "罓": "网", "罒": "网", "攵": "攴", "王": "玉", "尣": "尢",
    "歺": "歹", "耂": "老", "肀": "聿", "乚": "乙",
    "阝": "阜",   # left side; on the right side it is 邑 (#163)
    "钅": "金", "釒": "金", "饣": "食", "飠": "食",
    "讠": "言", "訁": "言", "纟": "糸", "糹": "糸",
}

SUPPLEMENT: frozenset[str] = frozenset(
    chr(cp) for cp in range(0x2E80, 0x2EF4) if unicodedata.name(chr(cp), None)
)

_NUMBER = {c: i + 1 for i, c in enumerate(KANGXI)}
_BY_NAME = {unicodedata.name(chr(0x2F00 + i)).removeprefix("KANGXI RADICAL "): c for i, c in enumerate(KANGXI)}


# Supplement names that differ from the Kangxi name of the same radical
_NAME_ALIAS = {"PERSON": "MAN", "MOTHER": "DO NOT", "CIVILIAN": "CLAN", "PAW": "CLAW", "RAM": "SHEEP", "EWE": "SHEEP"}


def _supplement_base(ch: str) -> str | None:
    """Base radical of a CJK Radicals Supplement character, if its Unicode name matches a Kangxi name.

    Characters whose name has no match (REPEAT, BOX, SNAKE, THREAD, CHOKE, MESH) are still radicals,
    but their base is left unknown rather than guessed.
    """
    name = unicodedata.name(ch, "").removeprefix("CJK RADICAL ")
    name = re.sub(r"^(?:[CJ]-)?SIMPLIFIED ", "", name)
    parts = name.split()
    if parts and parts[0] in _NAME_ALIAS:
        return _BY_NAME[_NAME_ALIAS[parts[0]]]
    while parts:
        if " ".join(parts) in _BY_NAME:
            return _BY_NAME[" ".join(parts)]
        parts.pop()                      # "WATER ONE" -> "WATER"
    return None


def base_radical(ch: str) -> str | None:
    """The Kangxi radical a character is or stands for, or None."""
    if ch in _NUMBER:
        return ch
    if ch in VARIANTS:
        return VARIANTS[ch]
    if ch in SUPPLEMENT:
        return _supplement_base(ch)
    return None


def radical_number(ch: str) -> int | None:
    """Kangxi number 1..214 of a radical or variant (None if not a radical, or base unknown)."""
    base = base_radical(ch)
    return _NUMBER.get(base) if base else None


def is_radical(ch: str) -> bool:
    """True for a Kangxi radical, a listed variant, or any CJK Radicals Supplement character."""
    return ch in _NUMBER or ch in VARIANTS or ch in SUPPLEMENT
