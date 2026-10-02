"""Pinyin with tone numbers ("hao3", "qiao2 / shao4") to pinyin with tone marks ("hǎo", "qiáo / shào")."""
from __future__ import annotations

import re

_MARKS = {"a": "āáǎà", "e": "ēéěè", "i": "īíǐì", "o": "ōóǒò", "u": "ūúǔù", "ü": "ǖǘǚǜ"}
_SYLLABLE = re.compile(r"([A-Za-zü:]+?)([1-5])?")


def syllable(s: str) -> str:
    """One syllable. Neutral tone (5, or none) carries no mark; "u:" and "v" are ü."""
    m = _SYLLABLE.fullmatch(s.strip())
    if not m:
        return s.strip()
    base, tone = m.group(1).replace("u:", "ü").replace("U:", "Ü"), m.group(2)
    base = re.sub(r"(?<=[nl])v", "ü", base)
    if not tone or tone == "5":
        return base
    low = base.lower()
    if "a" in low:
        at = low.index("a")
    elif "e" in low:
        at = low.index("e")
    elif "ou" in low:
        at = low.index("o")
    else:                                   # the last vowel takes the mark
        vowels = [i for i, ch in enumerate(low) if ch in _MARKS]
        if not vowels:
            return base
        at = vowels[-1]
    mark = _MARKS[low[at]][int(tone) - 1]
    return base[:at] + (mark.upper() if base[at].isupper() else mark) + base[at + 1:]


def readings(text: str | None) -> list[str]:
    """All readings of a string like "qiao2 / shao4" or "fo2; fu2", each converted. Several syllables in one reading
    ("bai3 ke4") are kept together."""
    if not text or not text.strip():
        return []
    out = []
    for reading in re.split(r"[/;]", text):
        syl = [syllable(x) for x in reading.split() if x]
        if syl:
            out.append(" ".join(syl))
    return out


def first_reading(text: str | None) -> str | None:
    r = readings(text)
    return r[0] if r else None
