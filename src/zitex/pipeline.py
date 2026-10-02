"""The workflow behind the Streamlit app: setup, extract, xelatex main.tex, and small helpers for pictures.

The three steps are the same commands a person types (`zitex setup`, `zitex extract`, `xelatex`), run as separate
processes, so the app does exactly what the tutorial describes.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .workspace import MAX_CHARS

SPLIT = re.compile(r"[,，、\s]+")


def parse_chars(text: str) -> list[str]:
    """Characters from a string such as "器,藻 佛": separated by commas or spaces, each once, in the order given."""
    return list(dict.fromkeys(c for c in SPLIT.split(text or "") if c))


@dataclass
class Step:
    name: str
    command: list[str]
    ok: bool
    output: str


@dataclass
class PipelineResult:
    ok: bool = False
    steps: list[Step] = field(default_factory=list)
    pdf: Path | None = None
    chars: list[str] = field(default_factory=list)       # the characters asked for, truncated to the cap
    truncated: int = 0                                   # how many were dropped by the cap
    missing: list[str] = field(default_factory=list)     # asked for, but not in the database (extract skipped them)
    message: str = ""

    @property
    def log(self) -> str:
        return "\n\n".join(f"$ {' '.join(s.command)}\n{s.output.strip()}" for s in self.steps)


def _run(cmd: list[str], cwd: Path | None, timeout: int) -> tuple[bool, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return False, f"{cmd[0]}: command not found"
    except subprocess.TimeoutExpired:
        return False, f"{cmd[0]} did not finish within {timeout} seconds"
    return p.returncode == 0, (p.stdout or "") + (p.stderr or "")


def generate_pdf(chars_text: str, db: str | Path, workdir: str | Path, *, timeout: int = 240,
                 on_step: Callable[[Step], None] | None = None) -> PipelineResult:
    """setup -> extract -> xelatex main.tex in `workdir`. Returns the result with every step's output.

    Each step runs even after a warning, but a step that fails stops the run. The folder is generated (extract
    overwrites), so it can be reused for the next list of characters.
    """
    res = PipelineResult()
    chars = parse_chars(chars_text)
    if not chars:
        res.message = "No characters given."
        return res
    res.truncated = max(0, len(chars) - MAX_CHARS)
    res.chars = chars[:MAX_CHARS]
    work = Path(workdir)
    work.mkdir(parents=True, exist_ok=True)

    def step(name: str, cmd: list[str], cwd: Path | None = None) -> bool:
        ok, out = _run(cmd, cwd, timeout)
        s = Step(name, cmd, ok, out)
        res.steps.append(s)
        if on_step:
            on_step(s)
        return ok

    zitex = [sys.executable, "-m", "zitex"]
    if not step("setup", [*zitex, "setup", "-o", str(work)]):
        res.message = "setup failed"
        return res
    extracted = step("extract", [*zitex, "extract", "-i", str(db), "-c", ",".join(res.chars), "-o", str(work)])
    res.missing = _skipped(res.steps[-1].output)
    if not extracted:
        res.message = "extract failed: " + _last_line(res.steps[-1].output)
        return res
    for stale in ("main.pdf", "main.aux", "main.log"):
        (work / stale).unlink(missing_ok=True)
    if shutil.which("xelatex") is None:
        res.message = "xelatex is not installed"
        return res
    step("xelatex", ["xelatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"], cwd=work)
    pdf = work / "main.pdf"
    if pdf.exists():
        res.pdf, res.ok = pdf, True
    else:
        res.message = "xelatex did not produce main.pdf: " + _last_line(_tex_error(work))
    return res


def _skipped(extract_output: str) -> list[str]:
    """The characters `zitex extract` reported as "not in <database>: 龘 …"."""
    found: list[str] = []
    for line in extract_output.splitlines():
        m = re.match(r"not in .*?: (.+)$", line.strip())
        if m:
            found += [c for c in SPLIT.split(m.group(1)) if c]
    return found


def _last_line(text: str) -> str:
    lines = [l for l in (text or "").strip().splitlines() if l.strip()]
    return lines[-1] if lines else ""


def _tex_error(work: Path) -> str:
    log = work / "main.log"
    if not log.exists():
        return ""
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    bang = [i for i, l in enumerate(lines) if l.startswith("!")]
    return "\n".join(lines[bang[0]: bang[0] + 4]) if bang else "\n".join(lines[-4:])


# ---- pictures --------------------------------------------------------------------------------------------------------

def pdf_to_pngs(pdf: str | Path, outdir: str | Path, dpi: int = 80) -> list[Path]:
    """The pages of a PDF as PNG files (needs pdftoppm). Returns [] when it is not available."""
    if shutil.which("pdftoppm") is None:
        return []
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("page-*.png"):
        old.unlink()
    ok, _ = _run(["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(outdir / "page")], None, 120)
    return sorted(outdir.glob("page-*.png")) if ok else []


def preview_png(entry, style: str = "matrix", lex=None, fonts=None, dpi: int = 110) -> bytes | None:
    """A picture of one entry (tree, matrix, formula or math) as PNG bytes, or None if xelatex or pdftoppm is missing."""
    if shutil.which("xelatex") is None or shutil.which("pdftoppm") is None:
        return None
    from .build import compile_pdf
    from .render import render_with
    kw: dict = {}
    if style in ("math", "formula"):
        kw.update(lang="en", lex=lex)
    snippet, _ = render_with(entry, style, fonts, **kw)
    with tempfile.TemporaryDirectory() as tmp:
        pdf = Path(tmp) / "p.pdf"
        if not compile_pdf(snippet, pdf, fonts.primary if fonts else "Noto Serif CJK SC", tmp):
            return None
        pngs = pdf_to_pngs(pdf, Path(tmp) / "png", dpi)
        return pngs[0].read_bytes() if pngs else None
