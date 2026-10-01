from pathlib import Path

from click.testing import CliRunner

from zitex.cli import main

DATA = str(Path(__file__).parent / "data" / "chars.yaml")


def test_check():
    r = CliRunner().invoke(main, ["check", DATA])
    assert r.exit_code == 0
    assert "29 entries, 0 warnings" in r.output


def test_shape():
    r = CliRunner().invoke(main, ["shape", DATA])
    assert r.exit_code == 0
    assert "品\t∴口口口" in r.output
    assert "哭\t∵口口犬" in r.output


# ---- build / render ----------------------------------------------------------

import shutil  # noqa: E402
import subprocess  # noqa: E402

import pytest  # noqa: E402

from zitex.build import scan_tex, snippet_name  # noqa: E402

LEX = str(Path(__file__).parent / "data" / "lexicon.yaml")


def test_snippet_name():
    assert snippet_name("藻", "tree") == "藻-tree"
    assert snippet_name("藻", "math", "fr") == "藻-math-fr"
    assert snippet_name("藻", "formula") == "藻-formula-en"


def test_scan_tex(tmp_path):
    t = tmp_path / "a.tex"
    t.write_text(r"\zi{藻} \zimath[lang=fr]{森} \zi[style=matrix]{國} \zitree{時} \ziformula{時}", encoding="utf-8")
    assert scan_tex(t) == {("藻", "tree", None, None), ("森", "math", "fr", None), ("國", "matrix", None, None),
                           ("時", "tree", None, None), ("時", "formula", None, None)}


def test_build_tex_all_styles(tmp_path):
    r = CliRunner().invoke(main, ["build", DATA, "-o", str(tmp_path), "-c", "藻,時", "-x", LEX, "-l", "en", "-l", "fr"])
    assert r.exit_code == 0, r.output
    names = sorted(p.name for p in tmp_path.glob("*.tex"))
    assert "藻-tree.tex" in names and "藻-matrix.tex" in names
    assert "藻-math-fr.tex" in names and "時-formula-en.tex" in names
    assert r"_{\text{algue}}" in (tmp_path / "藻-math-fr.tex").read_text(encoding="utf-8")
    assert "shí, temps" in (tmp_path / "時-formula-fr.tex").read_text(encoding="utf-8")
    assert not any(n.startswith("森") for n in names)  # only the requested characters


def test_build_reports_missing_char(tmp_path):
    r = CliRunner().invoke(main, ["build", DATA, "-o", str(tmp_path), "-c", "好", "-s", "tree"])
    assert r.exit_code == 0
    assert "好" in r.output  # reported on stderr, mixed into output by the runner


def test_build_rejects_unknown_style(tmp_path):
    r = CliRunner().invoke(main, ["build", DATA, "-o", str(tmp_path), "-s", "nope"])
    assert r.exit_code != 0


def test_render_stdout():
    r = CliRunner().invoke(main, ["render", "森", "-f", DATA, "-s", "math", "-x", LEX, "--collapse", "-l", "fr"])
    assert r.exit_code == 0
    assert r"3\times" in r.output and "arbre" in r.output


@pytest.mark.skipif(shutil.which("xelatex") is None, reason="xelatex not installed")
def test_sty_end_to_end(tmp_path):
    """A paper using zitex.sty: scan -> build -> xelatex."""
    sty = Path(__file__).parent.parent / "tex"
    doc = tmp_path / "main.tex"
    doc.write_text("\n".join([
        r"\documentclass{article}", r"\usepackage{zitex}", r"\begin{document}",
        r"\zi{藻}", r"\zimatrix{國}", r"\zimath{哭}", r"\zimath[lang=fr]{森}", r"\ziformula{時}", r"\zi{好}",
        r"\end{document}"]), encoding="utf-8")
    r = CliRunner().invoke(main, ["build", DATA, "--scan", str(doc), "-x", LEX, "-o", str(tmp_path / "zitex-out")])
    assert r.exit_code == 0, r.output
    env = {**__import__("os").environ, "TEXINPUTS": f"{sty}:"}
    p = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                       cwd=tmp_path, env=env, capture_output=True, text=True)
    assert p.returncode == 0, p.stdout[-1000:]
    assert "Missing character" not in p.stdout
    assert "Missing zitex-out" in p.stdout  # 好 is not built; a warning, not an error
    assert (tmp_path / "main.pdf").exists()


def test_render_result_option():
    below = CliRunner().invoke(main, ["render", "時", "-f", DATA, "-s", "math", "-x", LEX]).output
    paren = CliRunner().invoke(main, ["render", "時", "-f", DATA, "-s", "math", "-x", LEX, "--result", "paren"]).output
    assert r"_{\text{time}}" in below and r"\textit{time}" not in below
    assert r"\textit{time}" in paren



# ---- readings in build and the .sty ------------------------------------------------------

def test_snippet_name_with_reading():
    assert snippet_name("虹", "tree", reading="author") == "虹-tree@author"
    assert snippet_name("虹", "math", "fr", "author") == "虹-math-fr@author"


def test_scan_tex_reads_reading(tmp_path):
    t = tmp_path / "a.tex"
    t.write_text(r"\zimath[reading=dictionary]{虹} \zi[style=tree,reading=author]{虹}", encoding="utf-8")
    assert scan_tex(t) == {("虹", "math", None, "dictionary"), ("虹", "tree", None, "author")}


def test_build_with_reading(tmp_path):
    r = CliRunner().invoke(main, ["build", DATA, "-o", str(tmp_path), "-c", "虹", "-s", "tree,math", "-x", LEX,
                                  "--reading", "dictionary", "--arrow", "role"])
    assert r.exit_code == 0, r.output
    assert (tmp_path / "虹-tree@dictionary.tex").exists()
    assert "sound: gōng" in (tmp_path / "虹-math-en@dictionary.tex").read_text(encoding="utf-8")


def test_render_reading_option():
    a = CliRunner().invoke(main, ["render", "虹", "-f", DATA, "-s", "math", "-x", LEX, "--arrow", "role"]).output
    d = CliRunner().invoke(main, ["render", "虹", "-f", DATA, "-s", "math", "-x", LEX, "--arrow", "role",
                                  "--reading", "dictionary"]).output
    assert r"\xrightarrow" not in a and r"\xrightarrow" in d


@pytest.mark.skipif(shutil.which("xelatex") is None, reason="xelatex not installed")
def test_sty_reading_end_to_end(tmp_path):
    sty = Path(__file__).parent.parent / "tex"
    doc = tmp_path / "main.tex"
    doc.write_text("\n".join([r"\documentclass{article}", r"\usepackage{zitex}", r"\begin{document}",
                              r"\zimath[reading=dictionary]{虹}", r"\zitexsetreading{author}", r"\zitree{虹}",
                              r"\end{document}"]), encoding="utf-8")
    r = CliRunner().invoke(main, ["build", DATA, "--scan", str(doc), "-x", LEX, "--arrow", "role",
                                  "-o", str(tmp_path / "zitex-out")])
    assert r.exit_code == 0, r.output
    names = sorted(p.name for p in (tmp_path / "zitex-out").glob("*.tex"))
    assert names == ["虹-math-en@dictionary.tex", "虹-tree@author.tex"]
    env = {**__import__("os").environ, "TEXINPUTS": f"{sty}:"}
    p = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                       cwd=tmp_path, env=env, capture_output=True, text=True)
    assert p.returncode == 0, p.stdout[-800:]
    assert "Missing zitex-out" not in p.stdout and "Missing character" not in p.stdout


def test_scan_follows_setlang_and_setreading(tmp_path):
    t = tmp_path / "a.tex"
    t.write_text("\n".join([r"\zimath{森}", r"\zitexsetlang{fr}", r"\zimath{森}", r"\zimath[lang=en]{森}",
                            r"\zitexsetreading{author}", r"\zitree{虹}", r"\zitree[reading=dictionary]{虹}"]),
                 encoding="utf-8")
    assert scan_tex(t) == {("森", "math", None, None), ("森", "math", "fr", None), ("森", "math", "en", None),
                           ("虹", "tree", "fr", "author"), ("虹", "tree", "fr", "dictionary")}
