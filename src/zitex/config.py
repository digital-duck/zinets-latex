"""Settings from the environment or a ``.env`` file in the current folder (the environment wins).

  ZITEX_PICT_DIR     folder searched for ``u<hex>.png`` (also .jpg, .jpeg, .pdf, .svg) pictures, one per character
  ZITEX_PICT_HEIGHT  fixed height of the pict row in \\zimath[pict], a TeX length (default 1.8em)
  ZITEX_PICT_WIDTH   fixed width of each pict (default 1.8em); a picture is scaled to fit, keeping its shape
  ZITEX_MEANING_WIDTH  width a meaning phrase wraps at in \\zimath[pict] (default 6em)
  ZITEX_MEANING_SENSES how many '/'-separated senses of a meaning \\zimath[pict] shows (default 3; 0 = all)
  ZITEX_EMOJI_FONT   colour emoji font file used to turn an emoji pict into a picture (default: Noto Color Emoji)
"""
from __future__ import annotations

import os
import re
from pathlib import Path

DEFAULTS = {"ZITEX_PICT_HEIGHT": "1.8em", "ZITEX_PICT_WIDTH": "1.8em", "ZITEX_MEANING_WIDTH": "6em",
            "ZITEX_MEANING_SENSES": "3"}
_LENGTH = re.compile(r"^\d+(\.\d+)?(em|ex|pt|cm|mm|in|bp)$")


def _dotenv(path: str | Path = ".env") -> dict[str, str]:
    p = Path(path)
    if not p.is_file():
        return {}
    out = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip("'\"")
    return out


def get(name: str, default: str | None = None) -> str | None:
    """Environment variable, else the ``.env`` file, else the built-in default."""
    return os.environ.get(name) or _dotenv().get(name) or DEFAULTS.get(name, default)


def pict_length(name: str) -> str:
    """A TeX length setting; a value that is not a plain length falls back to the default."""
    v = get(name)
    return v if v and _LENGTH.match(v) else DEFAULTS[name]


def pict_dir() -> Path | None:
    v = get("ZITEX_PICT_DIR")
    return Path(v).expanduser() if v else None


def meaning_senses() -> int:
    v = get("ZITEX_MEANING_SENSES")
    return int(v) if v and v.isdigit() else int(DEFAULTS["ZITEX_MEANING_SENSES"])
