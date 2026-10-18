"""\\zimath[pict]: the pictmath grid (pinyin / character / meaning / pict), the lexicon's pict and meaning rules."""
import shutil
import subprocess
from pathlib import Path

import pytest
from PIL import Image

from zitex import Lexicon, load_yaml
from zitex.loader import entry_from_dict
from zitex.build import build, scan_tex, snippet_name
from zitex.lexicon import emoji_font
from zitex.render import document, math_chars, render

ENTRIES = {e.char: e for e in load_yaml(Path(__file__).parent / "data" / "chars.yaml")}


def _png(path: Path, size=(20, 50)):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, "black").save(path)
    return path


def _lex(tmp_path, **kw) -> Lexicon:
    lex = Lexicon(pict_dir=tmp_path / "picts", **kw)
    lex.pinyin.update({"日": "rì", "寺": "sì", "時": "shí"})
    lex.gloss.update({"日": {"en": "sun"}, "寺": {"en": "temple"}, "時": {"en": "time"}})
    return lex


def test_meaning_falls_back_from_gloss_to_concept_to_category_to_nothing():
    lex = Lexicon()
    assert lex.get_meaning("手") is None                       # a rare character: nothing
    lex.category["手"] = "HUMAN-BODY"
    assert lex.get_meaning("手") == "HUMAN-BODY"
    lex.concept["手"] = "HAND"
    assert lex.get_meaning("手") == "HAND"
    lex.gloss["手"] = {"en": "hand"}
    assert lex.get_meaning("手") == "hand"                     # a concrete phrase wins


def test_math_uses_the_same_meaning_fallback():
    lex = Lexicon()
    lex.concept["日"] = "SUN"
    assert r"_{\text{SUN}}" in render(ENTRIES["時"], "math", lex=lex)


def test_pict_prefers_image_then_emoji_then_nothing(tmp_path):
    lex = _lex(tmp_path)
    assert lex.pict_name("日") is None and lex.get_pict("日") is None
    lex.pict["日"] = "☀"
    if emoji_font():
        assert lex.get_pict("日") == ("emoji", "☀") and lex.pict_name("日") == "u65e5.png"
    _png(tmp_path / "picts" / f"u{ord('日'):x}.png")           # an image beats the emoji
    assert lex.get_pict("日")[0] == "image" and lex.pict_name("日") == "u65e5.png"


def test_lexicon_file_pict_is_relative_to_the_file(tmp_path):
    _png(tmp_path / "lex" / "sun.png")
    (tmp_path / "lex" / "lexicon.yaml").write_text("日: {pinyin: rì, concept: SUN, category: NATURE, pict: sun.png}\n",
                                                   encoding="utf-8")
    lex = Lexicon(pict_dir=None).merge_file(tmp_path / "lex" / "lexicon.yaml")
    assert (lex.concept["日"], lex.category["日"]) == ("SUN", "NATURE")
    assert lex.get_pict("日") == ("image", str(tmp_path / "lex" / "sun.png"))


def test_pictmath_is_a_grid_and_leaves_out_empty_rows(tmp_path):
    lex = _lex(tmp_path)
    s = render(ENTRIES["時"], "pictmath", lex=lex)
    assert r"\begin{array}" in s and s.count(r"\zipict{") == 0   # no pict anywhere: no pict row
    rows = s.split(r"\begin{array}")[1].split(r"\end{array}")[0].split(r"\\[0.8ex]")
    assert len(rows) == 3                                         # pinyin, characters, meanings
    _png(tmp_path / "picts" / f"u{ord('日'):x}.png")
    s = render(ENTRIES["時"], "pictmath", lex=lex)
    rows = s.split(r"\begin{array}")[1].split(r"\end{array}")[0].split(r"\\[0.8ex]")
    assert len(rows) == 4 and r"\zipict{u65e5.png}" in rows[3]    # the pict row, only 日 has one
    assert rows[3].count("&") == rows[1].count("&")               # every row has the same columns
    assert r"\providecommand\zipict[1]" in s


def test_pictmath_nested_composite_gets_a_column_per_part(tmp_path):
    s = render(ENTRIES["想"], "pictmath", lex=_lex(tmp_path))
    assert r"\Bigl(" in s and r"\Bigr)" in s
    assert s.split(r"\begin{array}")[1].split("\n")[0].count("c") >= 5   # 木 + 目 + 心 and the result, with operators


def test_pict_size_comes_from_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("ZITEX_PICT_HEIGHT", "3em")
    assert r"\providecommand\zipictheight{3em}" in render(ENTRIES["時"], "pictmath", lex=_lex(tmp_path))
    monkeypatch.setenv("ZITEX_PICT_HEIGHT", "huge")                # not a length: the default
    assert r"\providecommand\zipictheight{1.8em}" in render(ENTRIES["時"], "pictmath", lex=_lex(tmp_path))


def test_dotenv_file_is_read(tmp_path, monkeypatch):
    monkeypatch.delenv("ZITEX_PICT_WIDTH", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("# comment\nZITEX_PICT_WIDTH='2.5em'\n", encoding="utf-8")
    assert r"\providecommand\zipictwidth{2.5em}" in render(ENTRIES["時"], "pictmath", lex=_lex(tmp_path))


def test_senses_are_cut_and_the_meaning_wraps(tmp_path, monkeypatch):
    monkeypatch.setenv("ZITEX_MEANING_SENSES", "2")
    lex = _lex(tmp_path)
    lex.gloss["日"] = {"en": "sun/day/date/daytime"}
    s = render(ENTRIES["時"], "pictmath", lex=lex)
    assert "sun/day" in s and "date" not in s and r"\parbox[t]{\zimeaningwidth}" in s


def test_scan_finds_zimath_pict(tmp_path):
    t = tmp_path / "m.tex"
    t.write_text("\\zimath{時} \\zimath[pict]{時} \\zimath[lang=fr,pict=true]{日} \\zimath[pict=false]{寺} "
                 "\\zitree[pict]{日}\n", encoding="utf-8")
    assert scan_tex(t) == {("時", "math", None, None), ("時", "pictmath", None, None), ("日", "pictmath", "fr", None),
                           ("寺", "math", None, None), ("日", "tree", None, None)}
    assert snippet_name("時", "pictmath", "en") == "u6642-時-pictmath-en"


def test_build_stages_the_pictures_next_to_the_snippets(tmp_path):
    lex = _lex(tmp_path)
    _png(tmp_path / "picts" / f"u{ord('日'):x}.png")
    out = tmp_path / "out"
    res = build(list(ENTRIES.values()), out, {("時", "pictmath", "en", None)}, lex=lex)
    assert (out / "picts" / "u65e5.png").is_file() and not (out / "picts" / "u5bfa.png").exists()
    assert res.manifest[0]["picts"] == ["u65e5.png"]
    assert (out / "u6642-時-pictmath-en.tex").is_file()
    assert math_chars(ENTRIES["時"]) == ["時", "日", "寺"]


def test_pictmath_is_not_in_the_default_styles(tmp_path):
    res = build([ENTRIES["時"]], tmp_path / "o", lex=_lex(tmp_path))
    assert not any("pictmath" in p.name for p in res.tex)


@pytest.mark.skipif(shutil.which("xelatex") is None, reason="xelatex not installed")
def test_pictmath_compiles_with_xelatex_and_a_picture(tmp_path):
    lex = _lex(tmp_path)
    _png(tmp_path / "picts" / f"u{ord('日'):x}.png")
    snippet = render(ENTRIES["時"], "pictmath", lex=lex)
    lex.stage_picts(math_chars(ENTRIES["時"]), tmp_path)
    (tmp_path / "t.tex").write_text(document(snippet, standalone=False, zitexpath=str(tmp_path)), encoding="utf-8")
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "t.tex"], cwd=tmp_path,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-800:]


# ---- named sets of pictures: \zimath[pict=obs] -------------------------------------------------

def test_a_named_set_has_its_own_pictures_and_file_names(tmp_path):
    lex = _lex(tmp_path)
    lex.pict["日"] = "☀"
    _png(tmp_path / "obs" / "sun.png")
    (tmp_path / "obs" / "lexicon.yaml").write_text("日: {pict_obs: sun.png}\n", encoding="utf-8")
    lex.merge_file(tmp_path / "obs" / "lexicon.yaml")
    assert lex.get_pict("日", "obs") == ("image", str(tmp_path / "obs" / "sun.png"))
    assert lex.pict_name("日", "obs") == "u65e5-obs.png"
    assert lex.pict_name("寺", "obs") is None                    # nothing in this set for 寺
    if emoji_font():
        assert lex.pict_name("日") == "u65e5.png"                # the default set is untouched (the emoji)


def test_a_named_set_is_also_found_in_a_subfolder_of_the_pict_dir(tmp_path):
    lex = _lex(tmp_path)
    _png(tmp_path / "picts" / "obs" / f"u{ord('日'):x}.png")
    assert lex.pict_name("日", "obs") == "u65e5-obs.png" and lex.pict_name("日") is None


def test_pictmath_with_a_set_uses_that_sets_pictures_and_the_style_name_carries_it(tmp_path):
    lex = _lex(tmp_path)
    _png(tmp_path / "picts" / "obs" / f"u{ord('日'):x}.png")
    s = render(ENTRIES["時"], "pictmath-obs", lex=lex)
    assert r"\zipict{u65e5-obs.png}" in s
    assert snippet_name("時", "pictmath-obs", "zh") == "u6642-時-pictmath-obs-zh"


def test_scan_finds_a_named_set(tmp_path):
    t = tmp_path / "m.tex"
    t.write_text("\\zimath[pict=obs,lang=zh]{日} \\zimath[pict]{日} \\zimath[pict=false]{日}\n", encoding="utf-8")
    assert scan_tex(t) == {("日", "pictmath-obs", "zh", None), ("日", "pictmath", None, None), ("日", "math", None, None)}


def test_build_stages_a_named_set_next_to_the_default_one(tmp_path):
    lex = _lex(tmp_path)
    _png(tmp_path / "picts" / f"u{ord('日'):x}.png")
    _png(tmp_path / "picts" / "obs" / f"u{ord('日'):x}.png")
    out = tmp_path / "out"
    build(list(ENTRIES.values()), out, {("時", "pictmath", "en", None), ("時", "pictmath-obs", "en", None)}, lex=lex)
    assert (out / "picts" / "u65e5.png").is_file() and (out / "picts" / "u65e5-obs.png").is_file()
    assert (out / "u6642-時-pictmath-en.tex").is_file() and (out / "u6642-時-pictmath-obs-en.tex").is_file()


def test_several_sets_make_one_picture_row_each_in_the_order_given(tmp_path):
    lex = _lex(tmp_path)
    for name in ("obs", "seal", "kaiti"):
        _png(tmp_path / "picts" / name / f"u{ord('日'):x}.png")
    s = render(ENTRIES["時"], "pictmath-obs+seal+kaiti", lex=lex)
    rows = [r for r in s.split("\\\\[0.8ex]") if "\\zipict{" in r]
    assert [("u65e5-obs.png" in r, "u65e5-seal.png" in r, "u65e5-kaiti.png" in r) for r in rows] == [
        (True, False, False), (False, True, False), (False, False, True)]
    assert snippet_name("時", "pictmath-obs+seal+kaiti", "zh") == "u6642-時-pictmath-obs+seal+kaiti-zh"
    # a set that has nothing for any term leaves its row out; a set with a picture for some terms leaves the others empty
    assert s.count("zipict{") == 3 and render(ENTRIES["時"], "pictmath-obs+bronze", lex=lex).count("zipict{") == 1


def test_scan_collects_repeated_pict_keys_into_one_style(tmp_path):
    t = tmp_path / "m.tex"
    t.write_text("\\zimath[pict=obs,pict=seal,pict=kaiti,lang=zh]{日}\n", encoding="utf-8")
    assert scan_tex(t) == {("日", "pictmath-obs+seal+kaiti", "zh", None)}


def test_build_stages_every_set_and_reports_the_ones_missing_for_a_term(tmp_path):
    lex = _lex(tmp_path)
    for name in ("obs", "seal"):
        _png(tmp_path / "picts" / name / f"u{ord('日'):x}.png")
    out = tmp_path / "out"
    res = build(list(ENTRIES.values()), out, {("時", "pictmath-obs+seal", "en", None)}, lex=lex)
    assert (out / "picts" / "u65e5-obs.png").is_file() and (out / "picts" / "u65e5-seal.png").is_file()
    assert (out / "u6642-時-pictmath-obs+seal-en.tex").is_file()
    assert any("[seal]" in x and "寺" in x for x in res.no_pict)


def test_unknown_style_still_fails_with_a_set_name(tmp_path):
    with pytest.raises(ValueError):
        render(ENTRIES["時"], "mathx-obs", lex=_lex(tmp_path))


@pytest.mark.skipif(shutil.which("xelatex") is None, reason="xelatex not installed")
def test_zimath_pict_keys_pick_the_right_snippet_in_a_real_document(tmp_path):
    """\\zimath, \\zimath[pict] and \\zimath[pict=obs] read three different snippet files (the sty and Python agree)."""
    lex = _lex(tmp_path)
    _png(tmp_path / "picts" / f"u{ord('日'):x}.png")
    _png(tmp_path / "picts" / "obs" / f"u{ord('日'):x}.png")
    out = tmp_path / "zitex-out"
    _png(tmp_path / "picts" / "seal" / f"u{ord('日'):x}.png")
    jobs = {("時", "math", "en", None), ("時", "pictmath", "en", None), ("時", "pictmath-obs", "en", None),
            ("時", "pictmath-obs+seal", "en", None)}
    build(list(ENTRIES.values()), out, jobs, lex=lex)
    sty = Path(__file__).parents[1] / "src" / "zitex"
    (tmp_path / "t.tex").write_text(
        "\\documentclass{article}\\usepackage{zitex}\\begin{document}\n"
        "\\zimath{時}\\zimath[pict]{時}\\zimath[pict=obs]{時}\\zimath[lang=en,pict=false]{時}"
        "\\zimath[pict=obs,pict=seal]{時}\n\\end{document}\n",
        encoding="utf-8")
    import os
    env = {**os.environ, "TEXINPUTS": f"{sty}:"}
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "t.tex"], cwd=tmp_path,
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout[-800:]
    assert "Missing" not in r.stdout and "[時?]" not in r.stdout


def test_an_emoji_is_not_offered_when_pillow_is_missing(tmp_path, monkeypatch):
    """Without Pillow the emoji cannot be drawn, so no picture is named: a snippet must not point at a file that staging
    cannot write (XeLaTeX would stop on it)."""
    import builtins
    real_import = builtins.__import__

    def no_pillow(name, *a, **k):
        if name == "PIL" or name.startswith("PIL."):
            raise ImportError("no Pillow here")
        return real_import(name, *a, **k)

    lex = _lex(tmp_path)
    lex.pict["日"] = "☀"
    monkeypatch.setattr(builtins, "__import__", no_pillow)
    assert lex.get_pict("日") is None and lex.pict_name("日") is None
    assert r"\zipict{" not in render(ENTRIES["時"], "pictmath", lex=lex)


# ---- scanner and package must name the same files; unusable pictures are reported ----

def test_scan_ignores_spaces_in_options(tmp_path):
    from zitex.build import scan_tex
    f = tmp_path / "a.tex"
    f.write_text(r"\zimath[pict = obs, lang = zh]{明}", encoding="utf-8")
    assert scan_tex(f) == {("明", "pictmath-obs", "zh", None)}


def test_scan_without_lang_uses_en_even_when_l_is_zh(tmp_path):
    from click.testing import CliRunner
    from zitex.cli import main
    (tmp_path / "chars.yaml").write_text("- {char: 明, shape: \"⿰日月\"}\n", encoding="utf-8")
    (tmp_path / "a.tex").write_text(r"\zimath{明}", encoding="utf-8")
    r = CliRunner().invoke(main, ["render", "-i", str(tmp_path / "chars.yaml"), "--scan", str(tmp_path / "a.tex"),
                                  "-l", "zh", "-o", str(tmp_path / "out")])
    names = {p.name for p in (tmp_path / "out").glob("*.tex")}
    assert names == {"u660e-明-math-en.tex"}, (names, r.output)


def test_a_plain_word_as_pict_is_reported_not_promised(tmp_path):
    lex = _lex(tmp_path)
    lex.pict["日"] = "sun"
    assert lex.get_pict("日") is None and lex.pict_name("日") is None
    assert any("neither an image file nor an emoji" in p for p in lex.problems)


def test_a_missing_picture_file_is_reported(tmp_path):
    lex = _lex(tmp_path)
    lex.pict["日"] = "nosuch/u65e5.png"
    assert lex.get_pict("日") is None
    assert any("file not found" in p for p in lex.problems)


def test_set_names_must_not_contain_a_hyphen(tmp_path):
    import pytest
    f = tmp_path / "l.yaml"
    f.write_text("日: {pict_old-obs: x.png}\n", encoding="utf-8")
    with pytest.raises(ValueError):
        Lexicon().merge_file(f)


def test_set_names_must_not_contain_a_plus(tmp_path):
    f = tmp_path / "l.yaml"
    f.write_text("日: {pict_a+b: x.png}\n", encoding="utf-8")
    with pytest.raises(ValueError):
        Lexicon().merge_file(f)


def test_an_empty_lexicon_entry_is_skipped(tmp_path):
    f = tmp_path / "l.yaml"
    f.write_text("日:\n月: {pinyin: yuè}\n", encoding="utf-8")
    assert Lexicon().merge_file(f).pinyin == {"月": "yuè"}


def test_a_leaf_character_is_one_column(tmp_path):
    lex = _lex(tmp_path)
    for style in ("math", "pictmath"):
        leaf = entry_from_dict({"char": "日", "tree": {"c": "日"}})
        out = render(leaf, style, lex=lex)
        body = out.split("\\[", 1)[-1] if style == "pictmath" else out
        assert "=" not in body and "\\rightarrow" not in body, out


def test_a_codepoint_above_ffff_names_the_same_file(tmp_path):
    from zitex.build import snippet_name
    assert snippet_name("\U00020000", "math", "en", None) == "u20000-𠀀-math-en"
