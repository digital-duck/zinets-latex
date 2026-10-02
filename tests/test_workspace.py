import os
import shutil
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from zitex import fonts as fontmod
from zitex.cli import main
from zitex.fonts import FontChoice, FontConfig, detect_fonts
from zitex.loader import load_yaml
from zitex.workspace import MAX_CHARS, STY, TEMPLATES, fonts_yaml_text, make_main_tex, sty_state, write_setup

needs_xelatex = pytest.mark.skipif(shutil.which("xelatex") is None, reason="xelatex not installed")


def _run(args, cwd, env=None):
    old = os.getcwd()
    os.chdir(cwd)
    try:
        return CliRunner().invoke(main, args, env=env)
    finally:
        os.chdir(old)


# ---- finding fonts ---------------------------------------------------------------------------------------

def _fake_fonts(monkeypatch, installed: dict[str, set[int]]):
    monkeypatch.setattr(fontmod, "_font_files", lambda: {name: ("x", 0) for name in installed})
    monkeypatch.setattr(fontmod, "cmap", lambda fam: frozenset(installed[fam]) if fam in installed else None)


def test_detect_fonts_picks_the_first_candidate_and_greedy_fallbacks(monkeypatch):
    base = set(range(0x4E00, 0x4E40))
    _fake_fonts(monkeypatch, {
        "Noto Serif CJK SC": base,
        "Droid Sans Fallback": set(range(0x4E00, 0x4E10)),                  # adds nothing: left out
        "WenQuanYi Zen Hei": base | set(range(0x5000, 0x5010)),              # adds 16: comes first
        "Unifont": {0x20089, 0x20090, 0x20091},                              # adds 3
        "AR PL UMing CN": base | {0x20089, 0x20090},                         # adds 2, but Unifont already has both: left out
        "Hanazono Mincho A": {0x20089, 0x20092},                             # after Unifont adds only 0x20092
    })
    c = detect_fonts()
    assert c.primary == "Noto Serif CJK SC" and c.primary_size == len(base)
    assert c.fallbacks == [("WenQuanYi Zen Hei", 16), ("Unifont", 3), ("Hanazono Mincho A", 1)]   # greedy; nothing that adds none


def test_detect_fonts_without_the_preferred_primary(monkeypatch):
    _fake_fonts(monkeypatch, {"WenQuanYi Zen Hei": {0x4E00, 0x4E01}, "AR PL UMing CN": {0x4E00, 0x4E01, 0x4E02}})
    c = detect_fonts()
    assert c.primary == "WenQuanYi Zen Hei" and c.fallbacks == [("AR PL UMing CN", 1)]


def test_detect_fonts_finds_nothing(monkeypatch):
    _fake_fonts(monkeypatch, {"Some Latin Font": {0x41}})
    assert detect_fonts() == FontChoice(None)


# ---- the files setup writes --------------------------------------------------------------------------------

def test_fonts_yaml_loads_back_as_a_font_config(tmp_path):
    text = fonts_yaml_text(FontChoice("Noto Serif CJK SC", [("AR PL UMing CN", 102), ("Unifont", 94)], 30551))
    (tmp_path / "f.yaml").write_text(text, encoding="utf-8")
    cfg = FontConfig.load(tmp_path / "f.yaml")
    assert cfg.primary == "Noto Serif CJK SC" and cfg.fallbacks == ["AR PL UMing CN", "Unifont"]
    assert cfg.components["demo"] == {"svg": "glyphs/demo.svg"}                  # {demo} is stored without braces
    assert "30,551" in text and "AR PL UMing CN adds 102" in text and "\\setCJKmainfont" in text


def test_fonts_yaml_warns_when_no_font_was_found(tmp_path):
    text = fonts_yaml_text(FontChoice(None))
    (tmp_path / "f.yaml").write_text(text, encoding="utf-8")
    assert "WARNING" in text and FontConfig.load(tmp_path / "f.yaml").primary == "Noto Serif CJK SC"


def test_write_setup_writes_four_things_and_keeps_edited_files(tmp_path):
    choice = FontChoice("Noto Serif CJK SC", [("AR PL UMing CN", 5)], 100)
    res = write_setup(tmp_path / "work", choice)
    names = sorted(p.relative_to(tmp_path / "work").as_posix() for p in res.written)
    assert names == ["fallback.yaml", "fonts.yaml", "glyphs/demo.svg", "zitex.sty"] and res.kept == [] and res.sty == "installed"
    assert (tmp_path / "work" / "glyphs" / "demo.svg").read_bytes() == (TEMPLATES / "demo.svg").read_bytes()
    (tmp_path / "work" / "fonts.yaml").write_text("primary: Mine\n", encoding="utf-8")
    again = write_setup(tmp_path / "work", choice)
    assert again.written == [] and len(again.kept) == 3 and again.sty == "up to date"
    assert (tmp_path / "work" / "fonts.yaml").read_text() == "primary: Mine\n"
    forced = write_setup(tmp_path / "work", choice, force=True)
    assert len(forced.written) == 3 and "Noto Serif CJK SC" in (tmp_path / "work" / "fonts.yaml").read_text(encoding="utf-8")


def test_the_style_file_in_the_folder_is_the_packaged_one_and_stays_current(tmp_path):
    work = tmp_path / "work"
    write_setup(work, FontChoice(None))
    assert (work / "zitex.sty").read_bytes() == STY.read_bytes() and sty_state(work) == "local"
    (work / "zitex.sty").write_text("% an old version\n", encoding="utf-8")
    assert sty_state(work) == "stale"
    res = write_setup(work, FontChoice(None))                       # no --force needed: the style file must match zitex
    assert res.sty == "updated" and sty_state(work) == "local"
    assert sty_state(tmp_path / "elsewhere") == "absent"


def test_the_sample_entries_are_valid():
    entries = load_yaml(TEMPLATES / "fallback.yaml")
    assert [e.char for e in entries] == ["甲", "乙", "丙"] and entries[2].shape == "⿰日{demo}"


def test_setup_command(tmp_path):
    r = _run(["setup", "-o", "work"], tmp_path)
    assert r.exit_code == 0, r.output
    assert sorted(p.name for p in (tmp_path / "work").iterdir()) == ["fallback.yaml", "fonts.yaml", "glyphs", "zitex.sty"]
    assert "primary font:" in r.output and "next: zitex extract" in r.output and "install-sty" not in r.output
    again = _run(["setup", "-o", "work"], tmp_path)
    assert again.exit_code == 0 and again.output.count("kept ") == 3 and "zitex.sty in work is up to date" in again.output
    (tmp_path / "work" / "zitex.sty").write_text("% old\n", encoding="utf-8")
    assert "updated" in _run(["setup", "-o", "work"], tmp_path).output
    assert "wrote work/fonts.yaml" in _run(["setup", "-o", "work", "--force"], tmp_path).output.replace(str(tmp_path) + "/", "")


# ---- main.tex ----------------------------------------------------------------------------------------------

def test_make_main_tex():
    dicts = [{"char": "器", "pinyin": "qì", "meaning": "utensil; device"}, {"char": "半"}]
    tex = make_main_tex(dicts, "Noto Serif CJK SC")
    assert r"\documentclass{article}" in tex and r"\usepackage{zitex}" in tex and "@@" not in tex
    assert r"\setCJKmainfont{Noto Serif CJK SC}" in tex and r"\section*{zitex: 器 半}" in tex
    for cmd in (r"\zimath{器}", r"\zimatrix{器}", r"\ziformula{器}", r"\zitree{器}", r"\zitree{半}"):
        assert cmd in tex
    assert r"\subsection*{器 \normalfont\small(qì, utensil; device)}" in tex and r"\subsection*{半}" in tex
    assert tex.rstrip().endswith(r"\end{document}") and tex.count("{") == tex.count("}")


def test_make_main_tex_demo():
    dicts = [{"char": "器", "pinyin": "qì", "meaning": "utensil; device"}, {"char": "半"}]
    tex = make_main_tex(dicts, "Noto Serif CJK SC", "demo")
    assert "zitex in a research paper" in tex[:300] and r"\usepackage{zitex}" in tex and "@@" not in tex
    assert r"\setCJKmainfont{Noto Serif CJK SC}" in tex
    for cmd in (r"\zimath{器}", r"\zimatrix{器}", r"\ziformula{器}", r"\zitree{器}", r"\zitree{半}", r"\zimatrix{半}"):
        assert cmd in tex
    assert r"\subsection*{器 \normalfont\small(qì, utensil; device)}" in tex and r"\subsection*{半}" in tex
    assert "zitex extract -c 器,半 -o work/ --annotation demo" in tex and r"\zimatrix{器}\qquad\zimatrix{半}" in tex
    assert tex.rstrip().endswith(r"\end{document}")
    assert tex.count("{") - tex.count(r"\{") == tex.count("}") - tex.count(r"\}")


def test_make_main_tex_demo_with_one_character_and_with_many():
    one = make_main_tex([{"char": "好"}], "Font", "demo")
    assert r"\zimatrix{好}\qquad\zimatrix{好}" in one and "@@" not in one                    # the second example is the first again
    many = make_main_tex([{"char": chr(0x4e00 + i)} for i in range(20)], "Font", "demo")
    assert many.count(r"\resizebox{0.40\linewidth}") == 8 and "the first 8 of 20" in many   # the table is capped
    assert many.count(r"\subsection*{") == 20                                         # the catalogue has them all


def test_make_main_tex_rejects_an_unknown_annotation():
    with pytest.raises(ValueError, match="annotation"):
        make_main_tex([{"char": "好"}], "Font", "long")


def test_make_main_tex_escapes_the_meaning():
    tex = make_main_tex([{"char": "好", "meaning": "good & 100% fine_x #1"}], "Font")
    assert r"good \& 100\% fine\_x \#1" in tex


# ---- extract: the folder and main.tex ----------------------------------------------------------------------------

def test_extract_writes_main_tex_and_its_snippets(raw_db, tmp_path):
    _run(["setup", "-o", "work"], tmp_path)
    r = _run(["extract", "-i", str(raw_db), "-c", "器,時", "-o", "work"], tmp_path)
    assert r.exit_code == 0, r.output
    work = tmp_path / "work"
    assert {"chars.yaml", "lexicon.yaml", "main.tex", "fonts.yaml", "zitex.sty", "zitex-out"} <= {p.name for p in work.iterdir()}
    snippets = sorted(p.name for p in (work / "zitex-out").iterdir() if p.suffix == ".tex")
    assert (work / "zitex-out" / "build_manifest.json").exists()
    assert snippets == sorted(f"u{ord(c):x}-{s}" + (".tex" if s in ("matrix", "tree") else "-en.tex")
                              for c in "器時" for s in ("formula", "math", "matrix", "tree"))
    primary = FontConfig.load(work / "fonts.yaml").primary
    assert rf"\setCJKmainfont{{{primary}}}" in (work / "main.tex").read_text(encoding="utf-8")   # the font follows fonts.yaml
    assert "next: cd work && xelatex main.tex" in r.output and "warning" not in r.output


def test_extract_without_setup_uses_the_default_font_and_says_so(raw_db, tmp_path):
    r = _run(["extract", "-i", str(raw_db), "-c", "時", "-o", "work"], tmp_path)
    assert r.exit_code == 0 and "fonts.yaml" in r.output
    assert r"\setCJKmainfont{Noto Serif CJK SC}" in (tmp_path / "work" / "main.tex").read_text(encoding="utf-8")


def test_extract_warns_about_an_outdated_style_file(raw_db, tmp_path):
    _run(["setup", "-o", "work"], tmp_path)
    (tmp_path / "work" / "zitex.sty").write_text("% an old zitex.sty\n", encoding="utf-8")
    r = _run(["extract", "-i", str(raw_db), "-c", "時", "-o", "work"], tmp_path)
    assert r.exit_code == 0 and "differs from this version of zitex" in r.output and "zitex setup -o work" in r.output


def test_extract_keeps_at_most_max_chars_and_warns(raw_db, tmp_path, monkeypatch):
    import zitex.workspace as ws
    assert MAX_CHARS == 60
    monkeypatch.setattr(ws, "MAX_CHARS", 2)
    r = _run(["extract", "-i", str(raw_db), "-c", "器,時,藻,虹", "-o", "a"], tmp_path)
    assert r.exit_code == 0 and "4 characters found: keeping the first 2" in r.output and "-c" in r.output
    assert [e.char for e in load_yaml(tmp_path / "a" / "chars.yaml")] == ["器", "時"]                  # the first two, as named
    main_tex = (tmp_path / "a" / "main.tex").read_text(encoding="utf-8")
    assert r"\zimath{器}" in main_tex and r"\zimath{時}" in main_tex and r"\zimath{藻}" not in main_tex
    assert not any("藻" in p.name for p in (tmp_path / "a" / "zitex-out").iterdir())
    quiet = _run(["extract", "-i", str(raw_db), "-c", "器,時", "-o", "b"], tmp_path)                          # exactly the cap: no warning
    assert quiet.exit_code == 0 and "keeping the first" not in quiet.output


def test_extract_without_c_takes_the_first_characters_in_order(raw_db, tmp_path, monkeypatch):
    import zitex.workspace as ws
    monkeypatch.setattr(ws, "MAX_CHARS", 3)
    r = _run(["extract", "-i", str(raw_db), "-o", "a"], tmp_path)
    chars = [e.char for e in load_yaml(tmp_path / "a" / "chars.yaml")]
    everything = [e.char for e in __import__("zitex").sources.SqliteSource(raw_db).entries()]
    assert r.exit_code == 0 and chars == everything[:3] and "keeping the first 3" in r.output


def test_the_main_and_no_main_flags_are_gone(raw_db, tmp_path):
    for flag in ("--main", "--no-main"):
        assert _run(["extract", "-i", str(raw_db), "-c", "時", "-o", "w", flag], tmp_path).exit_code == 2


def test_extract_unknown_characters(raw_db, tmp_path):
    r = _run(["extract", "-i", str(raw_db), "-c", "時,龘", "-o", "work"], tmp_path)
    assert r.exit_code == 0 and "龘" in r.output
    assert _run(["extract", "-i", str(raw_db), "-c", "龘", "-o", "w2"], tmp_path).exit_code == 1
    assert not (tmp_path / "w2").exists()


# ---- the whole flow: setup, extract, xelatex main.tex ------------------------------------------------------------

@needs_xelatex
def test_setup_extract_then_xelatex_with_nothing_installed(raw_db, tmp_path):
    """The folder is self-contained: no TEXINPUTS, and zitex.sty is the copy next to main.tex."""
    assert _run(["setup", "-o", "work"], tmp_path).exit_code == 0
    r = _run(["extract", "-i", str(raw_db), "-c", "器,藻,時", "-o", "work"], tmp_path)
    assert r.exit_code == 0, r.output
    env = {k: v for k, v in os.environ.items() if k != "TEXINPUTS"}
    p = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                       cwd=tmp_path / "work", env=env, capture_output=True, text=True)
    assert p.returncode == 0, p.stdout[-800:]
    assert "Missing zitex-out" not in p.stdout and "Missing character" not in p.stdout
    assert "(./zitex.sty" in (tmp_path / "work" / "main.log").read_text(encoding="utf-8", errors="replace")   # the local copy
    text = subprocess.run(["pdftotext", str(tmp_path / "work" / "main.pdf"), "-"], capture_output=True, text=True).stdout \
        if shutil.which("pdftotext") else ""
    assert "?]" not in text                                          # no red [字?] placeholder: every snippet was found


# ---- --input and the default database ---------------------------------------------------------------------------

@pytest.fixture
def zx_db(raw_db, tmp_path):
    """The derived zx_ copy of the synthetic database, as `zitex db-build` writes it."""
    from zitex import zxdb
    (tmp_path / "built").mkdir()
    return zxdb.write_zx(zxdb.build_from_raw(raw_db), tmp_path / "built" / "zitex.sqlite3")


def test_extract_takes_its_database_with_input_only(raw_db, tmp_path):
    a = _run(["extract", "--input", str(raw_db), "-c", "時", "-o", "a"], tmp_path)
    b = _run(["extract", "-i", str(raw_db), "-c", "時", "-o", "b"], tmp_path)
    assert a.exit_code == b.exit_code == 0
    assert (tmp_path / "a" / "chars.yaml").read_text().split("\n\n", 1)[1] == (tmp_path / "b" / "chars.yaml").read_text().split("\n\n", 1)[1]
    bare = _run(["extract", str(raw_db), "-c", "時", "-o", "c"], tmp_path)                     # no positional argument any more
    assert bare.exit_code == 2 and "unexpected extra argument" in bare.output.lower() and not (tmp_path / "c").exists()
    assert _run(["extract", "-i", str(tmp_path / "missing.sqlite3"), "-c", "時", "-o", "d"], tmp_path).exit_code == 2


def _no_checkout_db(monkeypatch, tmp_path):
    """Pretend the zitex checkout has no db/ folder, so only the folders and $ZITEX_DB are searched."""
    import zitex.sources as sources
    monkeypatch.setattr(sources, "_checkout_root", lambda: tmp_path / "no-checkout")
    monkeypatch.delenv("ZITEX_DB", raising=False)


def test_extract_finds_db_zitex_sqlite3_in_this_folder_or_a_parent(zx_db, tmp_path, monkeypatch):
    _no_checkout_db(monkeypatch, tmp_path)
    project = tmp_path / "project"
    (project / "db").mkdir(parents=True)
    shutil.copy(zx_db, project / "db" / "zitex.sqlite3")
    (project / "work" / "deeper").mkdir(parents=True)
    for start in (project, project / "work", project / "work" / "deeper"):
        r = _run(["extract", "-c", "時", "-o", "out"], start)
        assert r.exit_code == 0, r.output
        assert "using the database" in r.output and str(project / "db" / "zitex.sqlite3") in r.output
        assert (start / "out" / "chars.yaml").exists()


def test_extract_database_from_the_environment(zx_db, tmp_path, monkeypatch):
    _no_checkout_db(monkeypatch, tmp_path)
    r = _run(["extract", "-c", "時", "-o", "out"], tmp_path, env={"ZITEX_DB": str(zx_db)})
    assert r.exit_code == 0 and str(zx_db) in r.output
    gone = _run(["extract", "-c", "時", "-o", "out2"], tmp_path, env={"ZITEX_DB": str(tmp_path / "missing.sqlite3")})
    assert gone.exit_code == 2                                                          # a missing $ZITEX_DB is ignored, then nothing is found


def test_extract_falls_back_on_the_zitex_checkout(zx_db, tmp_path, monkeypatch):
    import zitex.sources as sources
    checkout = tmp_path / "checkout"
    (checkout / "db").mkdir(parents=True)
    shutil.copy(zx_db, checkout / "db" / "zitex.sqlite3")
    monkeypatch.setattr(sources, "_checkout_root", lambda: checkout)
    monkeypatch.delenv("ZITEX_DB", raising=False)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    r = _run(["extract", "-c", "時", "-o", "out"], elsewhere)
    assert r.exit_code == 0 and str(checkout / "db" / "zitex.sqlite3") in r.output


def test_extract_with_no_database_says_where_it_looked(tmp_path, monkeypatch):
    _no_checkout_db(monkeypatch, tmp_path)
    empty = tmp_path / "empty"
    empty.mkdir()
    r = _run(["extract", "-c", "時", "-o", "out"], empty)
    assert r.exit_code == 2 and "--input" in r.output and "db/zitex.sqlite3" in r.output and "ZITEX_DB" in r.output
    assert not (empty / "out").exists()


def test_the_nearest_database_wins(zx_db, tmp_path, monkeypatch):
    from zitex.sources import find_default_database
    _no_checkout_db(monkeypatch, tmp_path)
    outer, inner = tmp_path / "outer", tmp_path / "outer" / "inner"
    for d in (outer, inner):
        (d / "db").mkdir(parents=True)
        shutil.copy(zx_db, d / "db" / "zitex.sqlite3")
    assert find_default_database(inner) == inner.resolve() / "db" / "zitex.sqlite3"
    assert find_default_database(outer) == outer.resolve() / "db" / "zitex.sqlite3"
    assert find_default_database(tmp_path / "nowhere") is None


# ---- render: --input and the default chars.yaml ------------------------------------------------------------------

def test_render_takes_its_input_with_input_only(tmp_path):
    data = Path(__file__).parent / "data" / "chars.yaml"
    a = _run(["render", "--input", str(data), "-c", "森", "-s", "tree", "-o", "-"], tmp_path)
    b = _run(["render", "-i", str(data), "-c", "森", "-s", "tree", "-o", "-"], tmp_path)
    assert a.exit_code == b.exit_code == 0 and a.output == b.output
    bare = _run(["render", str(data), "-c", "森", "-s", "tree", "-o", "-"], tmp_path)         # no positional argument any more
    assert bare.exit_code == 2 and "unexpected extra argument" in bare.output.lower()


def test_render_defaults_to_chars_yaml_in_this_folder(tmp_path):
    data = Path(__file__).parent / "data" / "chars.yaml"
    shutil.copy(data, tmp_path / "chars.yaml")
    r = _run(["render", "-c", "森", "-s", "tree", "-o", "-"], tmp_path)
    assert r.exit_code == 0 and r.output.startswith("\\definecolor")
    assert _run(["render", "-c", "森", "-s", "tree", "-o", "-", "-i", str(data)], tmp_path).output == r.output


def test_render_without_input_or_chars_yaml_says_what_to_do(tmp_path):
    r = _run(["render", "-c", "森", "-o", "-"], tmp_path)
    assert r.exit_code == 2 and "no chars.yaml" in r.output and "--input" in r.output
    assert list(tmp_path.iterdir()) == []


def test_render_does_not_fall_back_on_a_database(zx_db, tmp_path, monkeypatch):
    """Rendering every character of a 6000-character database by default would be a mistake, so there is no such default."""
    (tmp_path / "db").mkdir()
    shutil.copy(zx_db, tmp_path / "db" / "zitex.sqlite3")
    assert _run(["render", "-c", "時", "-o", "-"], tmp_path).exit_code == 2


# ---- every command reads its input the same way --------------------------------------------------------------------

@pytest.mark.parametrize("command", ["render", "extract", "check", "shape", "fonts", "patterns", "db-build"])
def test_no_command_takes_a_positional_argument(command, tmp_path):
    data = Path(__file__).parent / "data" / "chars.yaml"
    r = _run([command, "-i", str(data), "something.yaml"], tmp_path)          # a valid --input, plus a stray argument
    assert r.exit_code == 2 and "unexpected extra argument" in r.output.lower()


@pytest.mark.parametrize("command", ["render", "extract", "check", "shape", "fonts", "patterns", "db-build"])
def test_every_command_has_the_input_option(command):
    out = CliRunner().invoke(main, [command, "-h"], env={"COLUMNS": "100"}).output
    assert "-i, --input" in out


@pytest.mark.parametrize("command,extra", [("check", []), ("shape", []), ("fonts", []), ("patterns", []),
                                           ("render", ["-c", "森", "-s", "tree", "-o", "-"])])
def test_commands_default_to_chars_yaml_in_this_folder(command, extra, tmp_path):
    data = Path(__file__).parent / "data" / "chars.yaml"
    assert _run([command, *extra], tmp_path).exit_code == 2                                  # nothing here: it says so
    shutil.copy(data, tmp_path / "chars.yaml")
    r = _run([command, *extra], tmp_path)
    assert r.exit_code == 0, r.output
    assert r.output == _run([command, "-i", str(data), *extra], tmp_path).output.replace(str(data), "chars.yaml") or command == "check"


def test_check_takes_a_comma_separated_list_of_inputs(tmp_path):
    data = Path(__file__).parent / "data"
    one, two = str(data / "chars.yaml"), str(data / "fallback.yaml")
    for args in (["-i", f"{one},{two}"], ["-i", f"{one}, {two}"], ["--input", f"{one},{two},{one}"],
                 ["-i", one, "-i", two]):                                   # repeating -i adds to the list, as -c does
        r = _run(["check", *args], tmp_path)
        assert r.exit_code == 0, (args, r.output)
        assert r.output.count("29 entries") == 1 and r.output.count("3 entries") == 1      # each file once, in order
        assert r.output.index("29 entries") < r.output.index("3 entries")
    one_only = _run(["check", "-i", one], tmp_path)
    assert "29 entries" in one_only.output and "3 entries" not in one_only.output


def test_check_reports_a_missing_file_in_the_list(tmp_path):
    data = Path(__file__).parent / "data"
    r = _run(["check", "-i", f"{data / 'chars.yaml'},{tmp_path / 'nope.yaml'}"], tmp_path)
    assert r.exit_code == 2 and "nope.yaml" in r.output and "not a file" in r.output
    assert "entries" not in r.output                                       # nothing is checked until every name is good


def test_only_check_takes_a_list_and_the_others_take_one_file(tmp_path):
    data = Path(__file__).parent / "data"
    two = f"{data / 'chars.yaml'},{data / 'fallback.yaml'}"
    for command in ("shape", "patterns", "fonts"):
        assert _run([command, "-i", two], tmp_path).exit_code == 2


def test_db_build_needs_an_input_and_has_no_default(tmp_path):
    r = _run(["db-build"], tmp_path)
    assert r.exit_code == 2 and "--input" in r.output


def test_extract_annotation_demo_makes_a_paper_that_compiles(raw_db, tmp_path):
    if shutil.which("xelatex") is None:
        pytest.skip("xelatex not installed")
    assert _run(["setup", "-o", "work"], tmp_path).exit_code == 0
    r = _run(["extract", "-i", str(raw_db), "-c", "器,時", "-o", "work", "--annotation", "demo"], tmp_path)
    assert r.exit_code == 0, r.output
    work = tmp_path / "work"
    assert "research paper" in (work / "main.tex").read_text(encoding="utf-8")
    assert (work / "zitex-out" / "u5668-tree.tex").exists() and (work / "zitex-out" / "u6642-matrix.tex").exists()
    for _ in range(2):
        p = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"], cwd=work, capture_output=True, text=True)
        assert p.returncode == 0, p.stdout[-1500:]
    assert "Missing zitex-out" not in (work / "main.log").read_text(encoding="utf-8", errors="replace")
    assert (work / "main.pdf").stat().st_size > 5000
    again = _run(["extract", "-i", str(raw_db), "-c", "器", "-o", "work"], tmp_path)                       # default: minimal again
    assert again.exit_code == 0 and "research paper" not in (work / "main.tex").read_text(encoding="utf-8")
    assert _run(["extract", "-i", str(raw_db), "-o", "w9", "--annotation", "long"], tmp_path).exit_code == 2


def test_extract_takes_a_phrase_as_characters(raw_db, tmp_path):
    r = _run(["extract", "-i", str(raw_db), "-c", "器時", "-o", "work"], tmp_path)
    assert r.exit_code == 0, r.output
    assert [e.char for e in load_yaml(tmp_path / "work" / "chars.yaml")] == ["器", "時"]
