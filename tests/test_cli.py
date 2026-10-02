import os
import shutil
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from zitex.build import scan_tex, snippet_name
from zitex.cli import main

DATA = str(Path(__file__).parent / "data" / "chars.yaml")
LEX = str(Path(__file__).parent / "data" / "lexicon.yaml")
STY = Path(__file__).parent.parent / "src" / "zitex"
needs_xelatex = pytest.mark.skipif(shutil.which("xelatex") is None, reason="xelatex not installed")


def _render(args, tmp_path):
    """Run `zitex render DATA ...` inside tmp_path, so default output lands there."""
    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        return CliRunner().invoke(main, ["render", "-i", DATA, *args])
    finally:
        os.chdir(old)


def _names(path):
    """The snippet files in a folder (build_manifest.json, which every build writes, is checked on its own)."""
    return sorted(p.name for p in Path(path).iterdir() if p.name != "build_manifest.json")


# ---- check, shape ---------------------------------------------------------------------------

def test_check():
    r = CliRunner().invoke(main, ["check", "-i", DATA])
    assert r.exit_code == 0
    assert "29 entries, 0 warnings" in r.output


def test_shape():
    r = CliRunner().invoke(main, ["shape", "-i", DATA])
    assert r.exit_code == 0
    assert "品\t∴口口口" in r.output
    assert "哭\t∵口口犬" in r.output


def test_build_command_is_gone():
    assert CliRunner().invoke(main, ["build", DATA]).exit_code != 0


# ---- naming and scanning (library level) -----------------------------------------------------

def test_snippet_name():
    assert snippet_name("藻", "tree") == "u85fb-tree"
    assert snippet_name("藻", "math", "fr") == "u85fb-math-fr"
    assert snippet_name("藻", "formula") == "u85fb-formula-en"
    assert snippet_name("虹", "tree", reading="author") == "u8679-tree@author"
    assert snippet_name("虹", "math", "fr", "author") == "u8679-math-fr@author"


def test_scan_tex(tmp_path):
    t = tmp_path / "a.tex"
    t.write_text(r"\zi{藻} \zimath[lang=fr]{森} \zi[style=matrix]{國} \zitree{時} \ziformula{時}", encoding="utf-8")
    assert scan_tex(t) == {("藻", "tree", None, None), ("森", "math", "fr", None), ("國", "matrix", None, None),
                           ("時", "tree", None, None), ("時", "formula", None, None)}


def test_scan_tex_reads_reading(tmp_path):
    t = tmp_path / "a.tex"
    t.write_text(r"\zimath[reading=dictionary]{虹} \zi[style=tree,reading=author]{虹}", encoding="utf-8")
    assert scan_tex(t) == {("虹", "math", None, "dictionary"), ("虹", "tree", None, "author")}


def test_scan_follows_setlang_and_setreading(tmp_path):
    t = tmp_path / "a.tex"
    t.write_text("\n".join([r"\zimath{森}", r"\zitexsetlang{fr}", r"\zimath{森}", r"\zimath[lang=en]{森}",
                            r"\zitexsetreading{author}", r"\zitree{虹}", r"\zitree[reading=dictionary]{虹}"]),
                 encoding="utf-8")
    assert scan_tex(t) == {("森", "math", None, None), ("森", "math", "fr", None), ("森", "math", "en", None),
                           ("虹", "tree", "fr", "author"), ("虹", "tree", "fr", "dictionary")}


# ---- render: what is rendered ---------------------------------------------------------------

def test_render_everything_by_default(tmp_path):
    r = _render(["--emit", "tex", "-x", LEX], tmp_path)
    assert r.exit_code == 0, r.output
    names = _names(tmp_path / "zitex-out")                        # default folder: the one zitex.sty reads
    assert len(names) == 29 * 4                                   # every character, every style
    assert {"u85fb-tree.tex", "u85fb-matrix.tex", "u85fb-math-en.tex", "u85fb-formula-en.tex"} <= set(names)
    assert "29" in r.output or "116" in r.output


def test_render_char_selection(tmp_path):
    r = _render(["-c", "叕,作", "-x", LEX, "-o", "tmp/", "--emit", "tex"], tmp_path)     # the reported command
    assert r.exit_code == 0, r.output
    names = _names(tmp_path / "tmp")
    assert len(names) == 8 and {n.split("-")[0] for n in names} == {"u53d5", "u4f5c"}


@pytest.mark.parametrize("arg", [["-c", "叕,作"], ["--char", "叕,作"], ["--chars", "叕 作"], ["-c", "叕，作"],
                                 ["-c", "叕、作"], ["-c", "叕, 作"], ["-c", "叕", "-c", "作"], ["-c", "叕,作,叕"]])
def test_render_character_list_forms(tmp_path, arg):
    r = _render([*arg, "-s", "tree", "--emit", "tex", "-o", "o/"], tmp_path)
    assert r.exit_code == 0, r.output
    assert _names(tmp_path / "o") == ["u4f5c-tree.tex", "u53d5-tree.tex"]                    # duplicates are ignored


def test_render_some_characters_missing(tmp_path):
    r = _render(["-c", "叕,好,作", "-s", "tree", "--emit", "tex", "-o", "o/"], tmp_path)
    assert r.exit_code == 0 and "not in" in r.output and "好" in r.output
    assert _names(tmp_path / "o") == ["u4f5c-tree.tex", "u53d5-tree.tex"]
    assert _render(["-c", "好,也", "-s", "tree"], tmp_path).exit_code == 1               # none found


def test_render_styles(tmp_path):
    r = _render(["-c", "森", "-s", "tree,matrix", "--emit", "tex", "-o", "o/"], tmp_path)
    assert r.exit_code == 0 and _names(tmp_path / "o") == ["u68ee-matrix.tex", "u68ee-tree.tex"]
    assert _render(["-c", "森", "-s", "nope"], tmp_path).exit_code != 0


def test_render_languages(tmp_path):
    r = _render(["-c", "藻", "-x", LEX, "-l", "en", "-l", "fr", "--emit", "tex", "-o", "o/"], tmp_path)
    assert r.exit_code == 0, r.output
    assert _names(tmp_path / "o") == ["u85fb-formula-en.tex", "u85fb-formula-fr.tex", "u85fb-math-en.tex", "u85fb-math-fr.tex",
                                      "u85fb-matrix.tex", "u85fb-tree.tex"]                  # tree and matrix: one file
    assert r"_{\text{algue}}" in (tmp_path / "o" / "u85fb-math-fr.tex").read_text(encoding="utf-8")
    assert "shí, temps" in _render(["-c", "時", "-s", "formula", "-x", LEX, "-l", "fr", "-o", "-"], tmp_path).output


# ---- render: where the output goes ----------------------------------------------------------

def test_render_dash_prints_to_stdout(tmp_path):
    r = _render(["-c", "森", "-s", "math", "-x", LEX, "-o", "-"], tmp_path)
    assert r.exit_code == 0 and r.output.startswith(r"\[") and list(tmp_path.iterdir()) == []


def test_render_dash_needs_one_character_one_style_and_tex(tmp_path):
    assert _render(["-c", "森", "-s", "math,tree", "-o", "-"], tmp_path).exit_code == 2
    assert _render(["-c", "叕,作", "-s", "tree", "-o", "-"], tmp_path).exit_code == 2
    assert _render(["-c", "森", "-o", "-", "--emit", "pdf"], tmp_path).exit_code == 2
    assert list(tmp_path.iterdir()) == []


def test_render_suffix_picks_the_format(tmp_path):
    r = _render(["-c", "森", "-s", "math", "-x", LEX, "-o", "sen.tex"], tmp_path)
    assert r.exit_code == 0 and _names(tmp_path) == ["sen.tex"]
    assert (tmp_path / "sen.tex").read_text(encoding="utf-8").startswith(r"\[")


def test_render_a_file_defaults_to_the_tree_style(tmp_path):
    r = _render(["-c", "森", "-o", "sen.tex"], tmp_path)
    assert r.exit_code == 0 and "node" in (tmp_path / "sen.tex").read_text(encoding="utf-8")


def test_render_explicit_emit_overrides_the_suffix(tmp_path):
    r = _render(["-c", "森", "-s", "tree", "-o", "x.pdf", "--emit", "tex"], tmp_path)
    assert r.exit_code == 0 and _names(tmp_path) == ["x.tex"]


def test_render_bare_name_is_a_stem_for_one_output_and_a_directory_for_several(tmp_path):
    assert _render(["-c", "森", "-s", "tree", "-o", "sen", "--emit", "tex"], tmp_path).exit_code == 0
    assert (tmp_path / "sen.tex").is_file()
    assert _render(["-c", "森,作", "-s", "tree", "-o", "many", "--emit", "tex"], tmp_path).exit_code == 0
    assert _names(tmp_path / "many") == ["u4f5c-tree.tex", "u68ee-tree.tex"]
    assert _render(["-c", "森", "-o", "alltrees", "--emit", "tex"], tmp_path).exit_code == 0   # one char, all styles
    assert len(_names(tmp_path / "alltrees")) == 4


def test_render_existing_directory_needs_no_slash(tmp_path):
    (tmp_path / "existing").mkdir()
    assert _render(["-c", "森", "-o", "existing", "--emit", "tex"], tmp_path).exit_code == 0
    assert len(_names(tmp_path / "existing")) == 4


def test_render_several_outputs_cannot_go_to_one_file(tmp_path):
    assert _render(["-c", "叕,作", "-s", "tree", "-o", "x.tex"], tmp_path).exit_code == 2
    assert _render(["-c", "森", "-s", "tree,matrix", "-o", "x.tex"], tmp_path).exit_code == 2
    assert _render(["-c", "森", "-s", "math", "-l", "en", "-l", "fr", "-o", "x.tex"], tmp_path).exit_code == 2
    assert list(tmp_path.iterdir()) == []


def test_render_unknown_character_writes_nothing(tmp_path):
    assert _render(["-c", "好", "-o", "x.tex"], tmp_path).exit_code == 1
    assert list(tmp_path.iterdir()) == []


@needs_xelatex
def test_render_default_emit_is_both(tmp_path):
    r = _render(["-c", "叕", "-s", "math", "-x", LEX, "-o", "o/"], tmp_path)
    assert r.exit_code == 0, r.output
    assert _names(tmp_path / "o") == ["u53d5-math-en.pdf", "u53d5-math-en.tex"]
    assert (tmp_path / "o" / "u53d5-math-en.pdf").stat().st_size > 1000


@needs_xelatex
def test_render_pdf_suffix_and_bare_stem(tmp_path):
    # the command from an earlier report: -o 叕.tex --emit both
    r = _render(["-c", "叕", "-s", "math", "-x", LEX, "--show-pos", "-o", "叕.tex", "--emit", "both"], tmp_path)
    assert r.exit_code == 0, r.output
    assert _names(tmp_path) == ["叕.pdf", "叕.tex"]
    assert _render(["-c", "叕", "-s", "matrix", "-o", "m.pdf"], tmp_path).exit_code == 0
    assert "m.pdf" in _names(tmp_path) and "m.tex" not in _names(tmp_path)
    assert _render(["-c", "叕", "-s", "matrix", "-o", "both"], tmp_path).exit_code == 0           # no suffix: both
    assert {"both.tex", "both.pdf"} <= set(_names(tmp_path))


# ---- render: options -------------------------------------------------------------------------

def test_render_math_options(tmp_path):
    out = _render(["-c", "森", "-s", "math", "-x", LEX, "--collapse", "-l", "fr", "-o", "-"], tmp_path).output
    assert r"3\times" in out and "arbre" in out
    below = _render(["-c", "時", "-s", "math", "-x", LEX, "-o", "-"], tmp_path).output
    paren = _render(["-c", "時", "-s", "math", "-x", LEX, "--result", "paren", "-o", "-"], tmp_path).output
    assert r"_{\text{time}}" in below and r"\textit{time}" not in below and r"\textit{time}" in paren


def test_render_reading(tmp_path):
    a = _render(["-c", "虹", "-s", "math", "-x", LEX, "--arrow", "role", "-o", "-"], tmp_path).output
    d = _render(["-c", "虹", "-s", "math", "-x", LEX, "--arrow", "role", "--reading", "dictionary", "-o", "-"],
                tmp_path).output
    assert r"\xrightarrow" not in a and r"\xrightarrow" in d
    r = _render(["-c", "虹", "-s", "tree,math", "-x", LEX, "--reading", "dictionary", "--emit", "tex", "-o", "o/"],
                tmp_path)
    assert r.exit_code == 0 and _names(tmp_path / "o") == ["u8679-math-en@dictionary.tex", "u8679-tree@dictionary.tex"]


# ---- render --scan and the .sty --------------------------------------------------------------

def test_scan_rejects_conflicting_options(tmp_path):
    doc = tmp_path / "a.tex"
    doc.write_text(r"\zi{藻}", encoding="utf-8")
    for extra in (["-c", "森"], ["-s", "tree"], ["--reading", "x"], ["-o", "-"], ["-o", "x.tex"]):
        assert _render(["--scan", str(doc), *extra], tmp_path).exit_code == 2, extra


def test_scan_writes_snippets_only_by_default(tmp_path):
    doc = tmp_path / "a.tex"
    doc.write_text(r"\zi{藻} \zimath{森}", encoding="utf-8")
    r = _render(["--scan", str(doc), "-x", LEX], tmp_path)
    assert r.exit_code == 0, r.output
    assert _names(tmp_path / "zitex-out") == ["u68ee-math-en.tex", "u85fb-tree.tex"]            # tex: the paper is typeset by LaTeX


@needs_xelatex
def test_sty_end_to_end(tmp_path):
    """A paper using zitex.sty: render --scan, then xelatex."""
    doc = tmp_path / "main.tex"
    doc.write_text("\n".join([
        r"\documentclass{article}", r"\usepackage{zitex}", r"\begin{document}",
        r"\zi{藻}", r"\zimatrix{國}", r"\zimath{哭}", r"\zimath[lang=fr]{森}", r"\ziformula{時}", r"\zi{好}",
        r"\end{document}"]), encoding="utf-8")
    r = _render(["--scan", str(doc), "-x", LEX], tmp_path)                                  # default folder: zitex-out
    assert r.exit_code == 0, r.output
    env = {**os.environ, "TEXINPUTS": f"{STY}:"}
    p = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                       cwd=tmp_path, env=env, capture_output=True, text=True)
    assert p.returncode == 0, p.stdout[-1000:]
    assert "Missing character" not in p.stdout
    missing = [l for l in p.stdout.splitlines() if "Warning: Missing zitex-out" in l]
    assert len(missing) == 1 and f"u{ord('好'):x}-" in missing[0]      # only 好 is not rendered; a warning, not an error
    assert not any(n in p.stdout for n in ("u85fb-tree@", "u570b-matrix@", "u68ee-math-fr@"))   # no stray @ in a file name
    text = subprocess.run(["pdftotext", str(tmp_path / "main.pdf"), "-"], capture_output=True, text=True).stdout \
        if shutil.which("pdftotext") else "[好?]"
    assert "[藻" not in text and "[國" not in text and "[哭" not in text   # the figures are there, not placeholders


@needs_xelatex
def test_sty_reading_end_to_end(tmp_path):
    doc = tmp_path / "main.tex"
    doc.write_text("\n".join([r"\documentclass{article}", r"\usepackage{zitex}", r"\begin{document}",
                              r"\zimath[reading=dictionary]{虹}", r"\zitexsetreading{author}", r"\zitree{虹}",
                              r"\end{document}"]), encoding="utf-8")
    r = _render(["--scan", str(doc), "-x", LEX, "--arrow", "role"], tmp_path)
    assert r.exit_code == 0, r.output
    assert _names(tmp_path / "zitex-out") == ["u8679-math-en@dictionary.tex", "u8679-tree@author.tex"]
    env = {**os.environ, "TEXINPUTS": f"{STY}:"}
    p = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                       cwd=tmp_path, env=env, capture_output=True, text=True)
    assert p.returncode == 0, p.stdout[-800:]
    assert "Missing zitex-out" not in p.stdout and "Missing character" not in p.stdout


# ---- help text -------------------------------------------------------------------------------

@pytest.mark.parametrize("width", ["60", "80", "120"])
@pytest.mark.parametrize("command", [[], ["check"], ["shape"], ["fonts"], ["render"], ["install-sty"], ["patterns"], ["db-build"], ["extract"], ["setup"]])
def test_help_is_spelled_out(command, width):
    """No help page may cut its text short with '...' (click does that to a derived short help)."""
    r = CliRunner().invoke(main, [*command, "-h"], env={"COLUMNS": width})
    assert r.exit_code == 0
    assert "..." not in r.output and "…" not in r.output, r.output


def test_every_command_has_a_complete_one_line_summary():
    summaries = {name: cmd.short_help for name, cmd in main.commands.items()}
    assert set(summaries) == {"check", "shape", "fonts", "render", "install-sty", "patterns", "db-build", "extract", "setup", "review-export"}
    assert all(s and s.endswith(".") for s in summaries.values()), summaries


# ---- the default lexicon ---------------------------------------------------------------------

def test_render_uses_lexicon_yaml_from_the_current_folder(tmp_path):
    out_without = _render(["-c", "森", "-s", "math", "-o", "-"], tmp_path).output
    assert r"_{\text{tree}}" not in out_without                        # no lexicon here: pieces have no gloss
    shutil.copy(LEX, tmp_path / "lexicon.yaml")
    out_with = _render(["-c", "森", "-s", "math", "-o", "-"], tmp_path).output
    assert r"_{\text{tree}}" in out_with and r"\overset{\text{mù}}" in out_with


def test_render_x_replaces_the_default_lexicon(tmp_path):
    shutil.copy(LEX, tmp_path / "lexicon.yaml")
    mine = tmp_path / "mine.yaml"
    mine.write_text("木: {pinyin: mù, gloss: {en: wood}}\n", encoding="utf-8")
    out = _render(["-c", "森", "-s", "math", "-x", str(mine), "-o", "-"], tmp_path).output
    assert r"_{\text{wood}}" in out and r"_{\text{tree}}" not in out


def test_render_help_names_the_default_lexicon():
    r = CliRunner().invoke(main, ["render", "-h"], env={"COLUMNS": "100"})
    assert "./lexicon.yaml" in r.output


# ---- install-sty -----------------------------------------------------------------------------

def test_the_style_file_ships_inside_the_package():
    import zitex
    assert (Path(zitex.__file__).parent / "zitex.sty").is_file()


def test_install_sty_into_a_directory(tmp_path):
    r = CliRunner().invoke(main, ["install-sty", "--dir", str(tmp_path / "texmf")])
    assert r.exit_code == 0, r.output
    dest = tmp_path / "texmf" / "tex" / "latex" / "zitex" / "zitex.sty"
    assert dest.read_bytes() == (STY / "zitex.sty").read_bytes() and "installed" in r.output
    again = CliRunner().invoke(main, ["install-sty", "--dir", str(tmp_path / "texmf")])
    assert "already up to date" in again.output
    dest.write_text("% an old version\n", encoding="utf-8")
    assert "updated" in CliRunner().invoke(main, ["install-sty", "--dir", str(tmp_path / "texmf")]).output
    assert dest.read_bytes() == (STY / "zitex.sty").read_bytes()


@needs_xelatex
@pytest.mark.skipif(shutil.which("kpsewhich") is None, reason="kpsewhich not installed")
def test_install_sty_makes_plain_xelatex_work(tmp_path):
    """Default target is TEXMFHOME; after installing, xelatex needs no TEXINPUTS."""
    env = {**os.environ, "TEXMFHOME": str(tmp_path / "texmf")}
    r = CliRunner().invoke(main, ["install-sty"], env=env)
    assert r.exit_code == 0 and "TeX finds it" in r.output, r.output
    doc = tmp_path / "main.tex"
    doc.write_text("\n".join([r"\documentclass{article}", r"\usepackage{zitex}", r"\begin{document}",
                              r"\zimath{森}", r"\end{document}"]), encoding="utf-8")
    assert _render(["--scan", str(doc), "-x", LEX], tmp_path).exit_code == 0
    p = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                       cwd=tmp_path, env=env, capture_output=True, text=True)       # no TEXINPUTS
    assert p.returncode == 0, p.stdout[-600:]
    assert "Missing zitex-out" not in p.stdout          # the snippet was found: no stray @ in the name
    assert (tmp_path / "main.pdf").exists()


def test_scan_tex_skips_comments_and_verbatim(tmp_path):
    t = tmp_path / "p.tex"
    t.write_text("\\zimath{森}\n% \\zitree{木}  and \\zitexsetlang{fr}\n50\\% \\zimatrix{國}\n"
                 "\\begin{verbatim}\n\\zitexsetlang{de}\n\\zimath{藻}\n\\end{verbatim}\n\\zimath{悔}\n", encoding="utf-8")
    assert scan_tex(t) == {("森", "math", None, None), ("國", "matrix", None, None), ("悔", "math", None, None)}


def test_snippet_names_are_ascii_code_points():
    assert snippet_name("藻", "tree") == "u85fb-tree" and snippet_name("𠀉", "matrix") == "u20009-matrix"
    assert snippet_name("虹", "math", "fr", "author") == "u8679-math-fr@author"
    assert all(ord(c) < 128 for c in snippet_name("藻", "formula", "en", "dictionary"))


def test_build_manifest_maps_files_back_to_characters(tmp_path):
    import json
    r = _render(["-c", "藻,好", "-s", "tree,math", "--emit", "tex", "-x", LEX, "-o", "o/"], tmp_path)
    assert r.exit_code == 0, r.output
    m = json.loads((tmp_path / "o" / "build_manifest.json").read_text(encoding="utf-8"))
    files = {s["file"]: s for s in m["snippets"]}
    assert set(files) == {"u85fb-tree.tex", "u85fb-math-en.tex"} and files["u85fb-tree.tex"]["char"] == "藻"
    assert files["u85fb-tree.tex"]["codepoint"] == "U+85FB" and files["u85fb-math-en.tex"]["lang"] == "en"
    assert files["u85fb-tree.tex"]["lang"] is None and "好" not in json.dumps(m, ensure_ascii=False)
    assert all((tmp_path / "o" / f).exists() for f in files) and m["zitex_version"]
