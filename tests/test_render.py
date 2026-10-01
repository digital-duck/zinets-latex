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
    assert "左" in render_formula(ENTRIES["時"], show_pos=True, info=False)


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
    for lab in ("上", "下", "左", "右", "左下", "右下"):
        assert lab in s
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
