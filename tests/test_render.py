import shutil
import subprocess
from pathlib import Path

import pytest

from zitex import load_yaml
from zitex.render import document, esc, render, render_formula

DATA = Path(__file__).parent / "data" / "chars.yaml"
ENTRIES = {e.char: e for e in load_yaml(DATA)}


def test_formula():
    assert render_formula(ENTRIES["時"], info=False) == r"日 + 寺 $\rightarrow$ \textbf{時}"
    assert "(shí, time)" in render_formula(ENTRIES["時"])


def test_formula_anonymous_composite_in_brackets():
    assert render_formula(ENTRIES["想"], info=False).startswith("(木 + 目) + 心")


def test_formula_show_pos():
    assert "L" in render_formula(ENTRIES["時"], show_pos=True, info=False)


def test_esc():
    assert esc("a_b & 50%") == r"a\_b \& 50\%"


def test_unknown_style():
    with pytest.raises(ValueError):
        render(ENTRIES["時"], "nope")


@pytest.mark.parametrize("style", ["tree", "matrix"])
def test_snippets_are_balanced_and_standalone(style):
    for e in ENTRIES.values():
        s = render(e, style)
        assert s.count(r"\begin{tikzpicture}") == 1 and s.count(r"\end{tikzpicture}") == 1, e.char
        assert s.count("{") == s.count("}"), e.char  # TikZ needs balanced braces
        assert r"\documentclass" not in s


def test_tree_has_every_position_label():
    s = render(ENTRIES["藻"], "tree")
    for lab in ("U", "M", "L", "D", "LD", "RD"):
        assert f"{{{lab}}};" in s            # edge labels are node texts
    assert "喿" in s and "品" in s  # named nodes appear


@pytest.mark.skipif(shutil.which("xelatex") is None, reason="xelatex not installed")
@pytest.mark.parametrize("style", ["tree", "matrix"])
def test_compiles_with_xelatex(tmp_path, style):
    # one hard-ish character per style, covering ∴, named nodes and enclosures
    for ch in ("藻", "國", "哭"):
        tex = tmp_path / f"{ch}-{style}.tex"
        tex.write_text(document(render(ENTRIES[ch], style)), encoding="utf-8")
        r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error",
                            "-output-directory", str(tmp_path), str(tex)],
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stdout[-800:]
        assert tex.with_suffix(".pdf").exists()
        assert "Missing character" not in r.stdout, ch


# ---- math (equation) backend -------------------------------------------------

from zitex import load_lexicon  # noqa: E402
from zitex.render import render_math  # noqa: E402

LEX = load_lexicon(list(ENTRIES.values()), Path(__file__).parent / "data" / "lexicon.yaml")


def test_math_matches_conceptbook_grammar():
    s = render_math(ENTRIES["時"], LEX, wrap="none")
    assert s == (r"\underbrace{\overset{\text{rì}}{\text{日}}}_{\text{sun}} + "
                 r"\underbrace{\overset{\text{sì}}{\text{寺}}}_{\text{temple}} = "
                 r"\underbrace{\overset{\text{shí}}{\text{時}}}_{\text{time}}")
    p = render_math(ENTRIES["時"], LEX, wrap="none", result="paren")
    assert p.endswith(r"\overset{\text{shí}}{\text{時}}\ (\textit{time})")


def test_math_collapse_and_wrap():
    s = render_math(ENTRIES["品"], LEX, collapse=True)
    assert s.startswith(r"\[ 3\times ") and s.endswith(r"\]")
    assert s.count(r"\underbrace") == 2  # the repeated piece and the result
    assert render_math(ENTRIES["品"], LEX).count(r"\underbrace") == 4


def test_math_language_and_fallback():
    assert r"\text{arbre}" in render_math(ENTRIES["森"], LEX, lang="fr")
    assert r"_{\text{forêt}}" in render_math(ENTRIES["森"], LEX, lang="fr")
    # 想 has no fr gloss for 相-less parts it lacks nothing; an unknown language falls back to English
    assert r"\text{tree}" in render_math(ENTRIES["森"], LEX, lang="xx")


def test_math_role_arrow_uses_phonetic_pinyin():
    s = render_math(ENTRIES["悔"], LEX, arrow="role")
    assert r"\xrightarrow{\text{sound: měi}}" in s
    assert r"\xrightarrow{\text{son: měi}}" in render_math(ENTRIES["悔"], LEX, lang="fr", arrow="role")
    assert "=" in render_math(ENTRIES["森"], LEX, arrow="role")  # no roles -> plain equals


def test_math_anonymous_composite_in_brackets():
    assert r"\left(" in render_math(ENTRIES["想"], LEX)


def test_math_without_lexicon_still_works():
    s = render_math(ENTRIES["時"], None, wrap="none")
    # no lexicon: pieces have no gloss; the result still shows the entry's own meaning
    assert s.count(r"\underbrace") == 1 and r"_{\text{time}}" in s and "日" in s


def test_math_all_entries_balanced():
    for e in ENTRIES.values():
        s = render_math(e, LEX)
        assert s.count("{") == s.count("}"), e.char


@pytest.mark.skipif(shutil.which("xelatex") is None, reason="xelatex not installed")
def test_math_compiles_with_xelatex(tmp_path):
    body = "\n\n".join(render_math(ENTRIES[c], LEX, collapse=True, arrow="role", show_pos=True)
                       for c in ("時", "悔", "品", "藻", "愛", "哭"))
    tex = tmp_path / "m.tex"
    tex.write_text(document(body, standalone=False), encoding="utf-8")
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error",
                        "-output-directory", str(tmp_path), str(tex)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-800:]
    assert "Missing character" not in r.stdout


# ---- flat patterns -------------------------------------------------------------------

from zitex.render import flat_rects  # noqa: E402


def _inside(r):
    x, y, w, h = r
    return -1e-9 <= x and -1e-9 <= y and x + w <= 1 + 1e-9 and y + h <= 1 + 1e-9


def _overlap(a, b):
    return min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]) > 1e-9 and min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]) > 1e-9


@pytest.mark.parametrize("pattern", ["U-LD-RD", "LU-RU-D", "LU-RU-LD-RD", "LU-RU-M-LD-RD", "LU-LD-R", "L-RU-RD", "L-M-R"])
def test_flat_rects_fit_and_do_not_overlap(pattern):
    rs = flat_rects(pattern.split("-"))
    assert len(rs) == len(pattern.split("-")) and all(_inside(r) for r in rs)
    assert not any(_overlap(a, b) for i, a in enumerate(rs) for b in rs[i + 1:])


def test_flat_rects_geometry():
    top, lo_l, lo_r = flat_rects(["U", "LD", "RD"])
    assert top[1] > lo_l[1] and lo_l[0] < lo_r[0] and top[2] == 0.5     # apex up, centered
    a, b, c = flat_rects(["LU", "RU", "D"])
    assert a[1] == b[1] > c[1] and a[0] < b[0] and c[2] == 0.5          # apex down
    lu, ld, r = flat_rects(["LU", "LD", "R"])
    assert lu[1] > ld[1] and lu[0] == ld[0] < r[0]
    five = flat_rects(["LU", "RU", "M", "LD", "RD"])
    assert five[2][1] < five[0][1] and five[2][1] > five[3][1] and five[2][2] == 1.0   # M is the full-width middle row


def test_five_part_character_renders():
    e = ENTRIES["器"]
    assert e.tree.pattern == "LU-RU-M-LD-RD"
    assert render(e, "matrix").count(r"\node[] at") == 5
    assert "⁙" not in render(e, "tree")
    # a nested ⁙ has no glyph, so the tree shows its pattern instead
    from zitex.loader import entry_from_dict
    nested = entry_from_dict({"char": "X", "shape": "⿱艹⁙口口犬口口"})
    assert "LU-RU-M-LD-RD" in render(nested, "tree") and "⁙" not in render(nested, "tree")


@pytest.mark.skipif(shutil.which("xelatex") is None, reason="xelatex not installed")
def test_flat_patterns_compile(tmp_path):
    for ch in ("器", "叒", "叕", "哭"):
        for style in ("matrix", "tree"):
            tex = tmp_path / f"{ch}-{style}.tex"
            tex.write_text(document(render(ENTRIES[ch], style)), encoding="utf-8")
            r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error",
                                "-output-directory", str(tmp_path), str(tex)], capture_output=True, text=True)
            assert r.returncode == 0, r.stdout[-600:]
            assert "Missing character" not in r.stdout, (ch, style)


# ---- readings -------------------------------------------------------------------------

from zitex.loader import entry_from_dict, role_kinds  # noqa: E402


def test_entry_readings_and_default():
    e = ENTRIES["虹"]
    assert [r.name for r in e.readings] == ["author", "dictionary"]
    assert e.role == {"虫": "semantic", "工": "semantic"}                    # the first reading is the default
    assert e.roles_for("dictionary")["工"] == "phonetic"
    assert e.roles_for("nope") == e.role                                    # unknown reading: the default
    assert e.reading("dictionary").source.startswith("Shuowen")


def test_role_shorthand_is_a_default_reading():
    e = entry_from_dict({"char": "悔", "shape": "⿰忄每", "role": {"忄": "semantic", "每": "phonetic"}})
    assert [r.name for r in e.readings] == ["default"] and e.role["每"] == "phonetic"
    assert entry_from_dict({"char": "好", "shape": "⿰女子"}).role == {}


def test_role_kinds():
    assert role_kinds("semantic") == ["semantic"] and role_kinds(["semantic", "phonetic"]) == ["semantic", "phonetic"]
    assert role_kinds(None) == []


def test_reading_changes_math_arrow_and_colours():
    lex = LEX
    author = render_math(ENTRIES["虹"], lex, arrow="role")
    assert r"\xrightarrow" not in author and "= " in author               # 工 is semantic: plain equals
    with_reading = render(ENTRIES["虹"], "math", lex=lex, arrow="role", reading="dictionary")
    assert r"\xrightarrow{\text{sound: gōng}}" in with_reading
    # tree colours: 工 is semantic under "author" and phonetic under "dictionary"
    assert render(ENTRIES["虹"], "tree").count("fill=zi-semantic") == 2
    d = render(ENTRIES["虹"], "tree", reading="dictionary")
    assert d.count("fill=zi-semantic") == 1 and d.count("fill=zi-phonetic") == 1


def test_both_roles_get_their_own_colour():
    e = entry_from_dict({"char": "虹", "shape": "⿰虫工",
                         "readings": [{"name": "both", "role": {"虫": "semantic", "工": ["semantic", "phonetic"]}}]})
    s = render(e, "matrix")
    assert "zi-both" in s.replace("\\definecolor{zi-both}", "") and s.count("fill=zi-both") == 1


def test_reading_does_not_leak_between_renders():
    render(ENTRIES["虹"], "tree", reading="dictionary")
    assert render(ENTRIES["虹"], "tree").count("fill=zi-phonetic") == 0


def test_reading_validation():
    from zitex import validate_entry
    e = entry_from_dict({"char": "虹", "shape": "⿰虫工", "readings": [
        {"name": "a", "role": {"虫": "semantic", "木": "phonetic", "工": "magic"}},
        {"name": "a", "role": {}}]})
    assert sorted(w.code for w in validate_entry(e)) == ["W10", "W11", "W9"]
    assert validate_entry(ENTRIES["虹"]) == []


def test_reading_needs_a_name():
    from zitex import ParseError
    with pytest.raises(ParseError):
        entry_from_dict({"char": "虹", "shape": "⿰虫工", "readings": [{"role": {}}]})


def test_flat_rects_give_every_part_its_own_cell_when_rows_and_columns_mix():
    """Regression: in U-RU-M-R-RD (寝) the U part had no row or column group and was left at full size, behind the others."""
    from zitex.render import flat_rects
    for labels in (["U", "RU", "M", "R", "RD"], ["U", "L", "R"], ["D", "LU", "R"]):
        rects = flat_rects(labels)
        assert len(set(rects)) == len(labels), labels                            # no two parts share a rectangle
        assert not any(w == 1.0 and h == 1.0 for _, _, w, h in rects), labels   # and none is left at full size
        for i, (x, y, w, h) in enumerate(rects):                                 # and they do not overlap
            for x2, y2, w2, h2 in rects[i + 1:]:
                assert x + w <= x2 + 1e-9 or x2 + w2 <= x + 1e-9 or y + h <= y2 + 1e-9 or y2 + h2 <= y + 1e-9, labels
    assert flat_rects(["L", "R"]) == [(0.0, 0.0, 0.5, 1.0), (0.5, 0.0, 0.5, 1.0)]    # the usual patterns are unchanged
