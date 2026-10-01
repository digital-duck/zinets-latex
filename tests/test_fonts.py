import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from zitex import load_yaml, parse_ids, to_ids
from zitex.build import build
from zitex.cli import main
from zitex.fonts import FontConfig, coverage_report, covers, resolve
from zitex.render import render, render_with

D = Path(__file__).parent / "data"
CFG = FontConfig.load(D / "fonts.yaml")
FB = {e.char: e for e in load_yaml(D / "fallback.yaml")}

have_fonts = covers("Droid Sans Fallback", "日") is not None and covers("AR PL UMing CN", "日") is not None
needs_fonts = pytest.mark.skipif(not have_fonts, reason="test fonts (Droid Sans Fallback, AR PL UMing CN) not installed")


# ---- {name} components in ids ------------------------------------------------

def test_name_component_roundtrip():
    n = parse_ids("⿰日{demo}")
    assert n.parts[1].c == "demo" and n.parts[1].pos == "右"
    assert to_ids(n) == "⿰日{demo}"


def test_named_composite_with_name_component():
    n = parse_ids("⿰日{wide}(⿱一二)")
    assert n.parts[1].c == "wide" and n.parts[1].op == "⿱"
    assert to_ids(n) == "⿰日{wide}(⿱一二)"


@pytest.mark.parametrize("bad", ["{", "{}", "⿰日{abc"])
def test_name_component_errors(bad):
    from zitex import ParseError
    with pytest.raises(ParseError):
        parse_ids(bad)


# ---- resolution ---------------------------------------------------------------

def test_config_normalises_brace_keys():
    assert "demo" in CFG.components and "{demo}" not in CFG.components


def test_resolve_override_and_missing_name():
    assert resolve(CFG, "demo").kind == "svg"
    assert resolve(FontConfig(), "nope").kind == "missing"  # a name with no override


@needs_fonts
def test_resolve_fallback_and_missing():
    assert resolve(CFG, "日").kind == "plain"
    r = resolve(CFG, "\U00020089")
    assert (r.kind, r.value) == ("font", "AR PL UMing CN")
    assert resolve(CFG, "\U00020009").kind == "missing"


def test_alias_override():
    cfg = FontConfig(components={"甲": {"alias": "日"}})
    assert resolve(cfg, "甲").kind == "alias"
    s, _ = render_with(FB["甲"], "formula", cfg)
    assert "日 + \U00020089" in s


# ---- rendering ------------------------------------------------------------------

@needs_fonts
@pytest.mark.parametrize("style", ["tree", "matrix", "math", "formula"])
def test_fallback_markup(style):
    s = render(FB["甲"], style, CFG)
    assert "\\zifont{1}{AR PL UMing CN}{\U00020089}" in s
    assert s.startswith(r"\providecommand\zitexpath")  # snippet carries what it needs


@needs_fonts
def test_missing_markup_and_report():
    s, res = render_with(FB["乙"], "tree", CFG)
    assert r"\zimissing{U+20009}" in s
    assert res.missing == {"\U00020009"}


def test_svg_markup():
    s, res = render_with(FB["丙"], "matrix", CFG)
    assert r"\zisvg{demo.pdf}" in s and res.svgs == {"glyphs/demo.svg"}


def test_no_prelude_when_nothing_special():
    e = load_yaml(D / "chars.yaml")[0]
    assert r"\providecommand" not in render(e, "tree", FontConfig())


# ---- report and CLI ---------------------------------------------------------------

def test_real_data_fully_covered_by_default_font():
    rep = coverage_report(load_yaml(D / "chars.yaml"), FontConfig())
    if rep.inspected:
        assert rep.missing == []


@needs_fonts
def test_fonts_command_and_strict():
    r = CliRunner().invoke(main, ["fonts", str(D / "fallback.yaml"), "--fonts", str(D / "fonts.yaml")])
    assert r.exit_code == 0
    assert "MISSING" in r.output and "font AR PL UMing CN" in r.output and "svg glyphs/demo.svg" in r.output
    r = CliRunner().invoke(main, ["fonts", str(D / "fallback.yaml"), "--fonts", str(D / "fonts.yaml"), "--strict"])
    assert r.exit_code == 1


# ---- build ------------------------------------------------------------------------

@pytest.mark.skipif(shutil.which("inkscape") is None or shutil.which("xelatex") is None or not have_fonts,
                    reason="needs inkscape, xelatex and the test fonts")
def test_build_pdf_with_fallbacks(tmp_path):
    res = build(list(FB.values()), tmp_path, chars=["甲", "乙", "丙"], styles=["tree", "math"], emit="both", fonts=CFG)
    assert (tmp_path / "glyphs" / "demo.pdf").exists()
    assert not res.failed and len(res.pdf) == 6
    assert res.glyph_missing == ["\U00020009"]
