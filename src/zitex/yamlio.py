"""Write entries and a lexicon as YAML, in the compact style of the hand-written chars.yaml."""
from __future__ import annotations

import json
import re
import unicodedata


def _q(s: str) -> str:
    """A double-quoted YAML string (JSON is valid YAML), with non-ASCII characters left readable."""
    return json.dumps(s, ensure_ascii=False)


def _plain_ok(s: str) -> bool:
    return bool(s) and (re.fullmatch(r"[A-Za-z0-9_]+", s) is not None
                        or all(unicodedata.category(ch) == "Lo" for ch in s))


def _key(s: str) -> str:
    return s if _plain_ok(s) else _q(s)


def _leaf(n: dict) -> str:
    return "{c: %s, pos: %s}" % (_key(n["c"]), n["pos"])


def _map(n: dict, ind: int) -> list[str]:
    """Block-style lines for a branch, starting at indent `ind`."""
    sp = " " * ind
    lines = []
    if n.get("c"):
        lines.append(f"{sp}c: {_key(n['c'])}")
    op = n["op"]
    lines.append(f"{sp}op: {_q(op) if op.startswith('<') else op}")
    if n.get("pos"):
        lines.append(f"{sp}pos: {n['pos']}")
    parts = n["parts"]
    if all("op" not in p for p in parts):
        lines.append(sp + "parts: [" + ", ".join(_leaf(p) for p in parts) + "]")
    else:
        lines.append(sp + "parts:")
        for p in parts:
            if "op" not in p:
                lines.append(f"{sp}  - {_leaf(p)}")
            else:
                sub = _map(p, ind + 4)
                lines.append(f"{sp}  - " + sub[0].lstrip())
                lines.extend(sub[1:])
    return lines


def dump_entries(dicts: list[dict], header: str = "") -> str:
    out = [header.rstrip("\n")] if header else []
    for d in dicts:
        out.append("")
        out.append(f"- char: {_key(d['char'])}")
        for k in ("pinyin", "meaning"):
            if d.get(k):
                out.append(f"  {k}: {_q(d[k])}")
        out.append(f"  shape: {_q(d['shape'])}")
        t = d["tree"]
        if "op" in t:
            out.append("  tree:")
            out.extend(_map(t, 4))
        else:
            out.append(f"  tree: {{c: {_key(t['c'])}}}")
        for k in ("note", "review"):
            if d.get(k):
                out.append(f"  {k}: {_q(d[k])}")
    return "\n".join(out).lstrip("\n") + "\n"


def dump_lexicon(lex: dict[str, dict], header: str = "") -> str:
    out = [header.rstrip("\n")] if header else []
    for ch, v in lex.items():
        bits = []
        if v.get("pinyin"):
            bits.append(f"pinyin: {_q(v['pinyin'])}")
        if v.get("gloss"):
            bits.append("gloss: {" + ", ".join(f"{lang}: {_q(text)}" for lang, text in v["gloss"].items()) + "}")
        out.append(f"{_key(ch)}: {{{', '.join(bits)}}}")
    return "\n".join(out) + "\n"
