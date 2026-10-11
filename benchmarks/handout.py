#!/usr/bin/env python3
"""Benchmark: one edit to the data, regenerated across a handout of equations.

Builds a handout of N equations (``\\zimath{X}``, the characters that contain a chosen component, from the ZiNets
database), then edits ONE lexicon entry (the gloss of that component) and rebuilds. Reports, for each step, the
wall-clock time and how many snippet files changed, and counts the places a hand-made figure set would need editing.

    python benchmarks/handout.py                 # 40 equations, component 口, work folder in a temp dir
    python benchmarks/handout.py -n 50 -p 木 -w /tmp/handout

Needs xelatex and db/zitex.sqlite3 (or $ZITEX_DB). The numbers depend on the machine: run it on yours.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENV = {**os.environ, "PYTHONPATH": f"{REPO / 'src'}{os.pathsep}{os.environ.get('PYTHONPATH', '')}",
       "TEXINPUTS": f"{REPO / 'src' / 'zitex'}{os.pathsep}{os.environ.get('TEXINPUTS', '')}"}


def run(cmd, cwd):
    t = time.perf_counter()
    r = subprocess.run(cmd, cwd=cwd, env=ENV, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"failed: {' '.join(map(str, cmd))}\n{r.stdout[-600:]}\n{r.stderr[-600:]}")
    return time.perf_counter() - t


def zitex(*args, cwd):
    return run([sys.executable, "-m", "zitex", *args], cwd)


def pick(db: Path, part: str, n: int) -> list[str]:
    """Characters with a gloss and exactly two parts, one of them `part`, in code-point order."""
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = con.execute(
        "SELECT c.zi FROM zx_char c JOIN zx_part p ON p.zi = c.zi AND p.part = ? "
        "WHERE c.gloss_en IS NOT NULL AND c.gloss_en != '' AND (SELECT count(*) FROM zx_part q WHERE q.zi = c.zi) = 2 "
        "ORDER BY c.zi", (part,)).fetchall()
    return [r[0] for r in rows][:n]


def digests(folder: Path) -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.glob("*.tex"))}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("-n", type=int, default=40, help="number of equations")
    ap.add_argument("-p", "--part", default="口", help="the component whose gloss is edited")
    ap.add_argument("-w", "--work", type=Path, help="work folder (default: a temporary one)")
    ap.add_argument("-i", "--input", type=Path, default=Path(os.environ.get("ZITEX_DB", REPO / "db" / "zitex.sqlite3")))
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    a = ap.parse_args()
    if not shutil.which("xelatex"):
        sys.exit("xelatex not found")
    work = a.work or Path(tempfile.mkdtemp(prefix="zitex-handout-"))
    work.mkdir(parents=True, exist_ok=True)
    chars = pick(a.input, a.part, a.n)
    if len(chars) < a.n:
        print(f"only {len(chars)} characters match", file=sys.stderr)

    # the data: chars.yaml and lexicon.yaml extracted from the database (this step is not timed: it is data preparation)
    zitex("extract", "-i", str(a.input), "-c", ",".join(chars), "-o", str(work), cwd=work)
    chars = re.findall(r"^- char: (\S)", (work / "chars.yaml").read_text(encoding="utf-8"), re.M)   # those extract kept
    body = "\n".join(rf"\zimath{{{c}}}\par\medskip" for c in chars)
    (work / "main.tex").write_text(
        "\\documentclass{article}\n\\usepackage{zitex}\n\\usepackage[margin=2cm]{geometry}\n\\setlength{\\parindent}{0pt}\n"
        f"\\begin{{document}}\n{body}\n\\end{{document}}\n", encoding="utf-8")
    shutil.rmtree(work / "zitex-out", ignore_errors=True)

    def build():
        t_render = zitex("render", "-i", "chars.yaml", "--scan", "main.tex", "-x", "lexicon.yaml", "-o", "zitex-out", cwd=work)
        t_tex = run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"], work)
        return t_render, t_tex

    r0, x0 = build()
    before = digests(work / "zitex-out")

    # one edit: the gloss of the component
    lex = work / "lexicon.yaml"
    text = lex.read_text(encoding="utf-8")
    m = re.search(rf"^{re.escape(a.part)}:.*?\n(?=\S|\Z)", text, re.S | re.M)
    if not m:
        sys.exit(f"{a.part} has no entry in lexicon.yaml; choose another component with -p")
    old_entry = m.group(0)
    new_entry = re.sub(r"(en:\s*)(\"?)([^\"\n]+)(\"?)", lambda g: f'{g.group(1)}"{g.group(3).strip()} (edited)"', old_entry, count=1)
    if new_entry == old_entry:
        sys.exit(f"could not find an English gloss for {a.part} in lexicon.yaml")
    lex.write_text(text.replace(old_entry, new_entry), encoding="utf-8")

    r1, x1 = build()
    after = digests(work / "zitex-out")
    changed = sorted(k for k in after if before.get(k) != after[k])
    res = {
        "equations": len(chars), "edited_component": a.part, "snippets": len(after), "snippets_changed": len(changed),
        "edits_to_data": 1, "first_build_s": {"zitex": round(r0, 2), "xelatex": round(x0, 2)},
        "rebuild_after_one_edit_s": {"zitex": round(r1, 2), "xelatex": round(x1, 2)},
        "machine": f"{platform.system()} {platform.machine()}, Python {platform.python_version()}",
        "work": str(work),
    }
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
        return
    print(f"{len(chars)} equations from the database, each containing {a.part}; work folder {work}")
    print(f"first build:            zitex {r0:5.2f} s + xelatex {x0:5.2f} s, {len(after)} snippets")
    print(f"one edit to the gloss of {a.part}: 1 line in lexicon.yaml")
    print(f"rebuild:                zitex {r1:5.2f} s + xelatex {x1:5.2f} s, {len(changed)} of {len(after)} snippets changed")
    print(f"by hand, the same correction touches {len(changed)} equations in the .tex source.")


if __name__ == "__main__":
    main()
