import hashlib
import shutil
import sqlite3
from pathlib import Path

import pytest
from click.testing import CliRunner

from zitex import zxdb
from zitex.cli import main
from zitex.loader import load_yaml
from zitex.pinyin import first_reading, readings, syllable
from zitex.sources import SqliteSource, YamlSource, is_sqlite, open_source
from zitex.tree import node_to_dict
from zitex.validate import validate_entry
from zitex.yamlio import dump_entries, dump_lexicon

DATA = Path(__file__).parent / "data"
import os

# an optional smoke test on the real database (not in the repository): set ZITEX_REAL_DB to its path
REAL_DB = Path(os.environ.get("ZITEX_REAL_DB", Path(__file__).parent.parent / "db" / "zi.sqlite3"))


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---- pinyin ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("raw,marked", [("hao3", "hǎo"), ("shang4", "shàng"), ("xie4", "xiè"), ("nu:3", "nǚ"), ("lv4", "lǜ"),
                                        ("gui1", "guī"), ("liu2", "liú"), ("ma5", "ma"), ("zhuang1", "zhuāng"),
                                        ("hou4", "hòu"), ("er2", "ér"), ("ao3", "ǎo")])
def test_pinyin_syllables(raw, marked):
    assert syllable(raw) == marked


def test_pinyin_readings():
    assert readings("qiao2 / shao4") == ["qiáo", "shào"]
    assert readings("fo2; fu2") == ["fó", "fú"] and readings("bai3 ke4") == ["bǎi kè"]
    assert first_reading("gùn / gǔn") == "gùn"            # already marked: kept
    assert first_reading("") is None and first_reading(None) is None


# ---- the two adapters --------------------------------------------------------------------------------

def test_open_source_recognises_a_database_by_its_header(raw_db, tmp_path):
    odd = tmp_path / "data.txt"
    shutil.copy(raw_db, odd)
    assert is_sqlite(odd) and isinstance(open_source(odd), SqliteSource)
    assert not is_sqlite(DATA / "chars.yaml") and isinstance(open_source(DATA / "chars.yaml"), YamlSource)


def test_yaml_source():
    src = YamlSource(DATA / "chars.yaml")
    assert len(src.entries()) == 29
    assert src.lexicon([DATA / "lexicon.yaml"]).get_gloss("木") == "tree"


def test_sqlite_source_builds_the_same_entries_a_yaml_file_would(raw_db):
    src = SqliteSource(raw_db)
    by = {e.char: e for e in src.entries()}
    assert src.from_raw
    assert by["時"].shape == "⿰日寺" and by["時"].tree.pattern == "L-M"          # 寺 is elemental: not expanded
    assert by["時"].pinyin == "shí" and by["時"].meaning == "time; period; hour"
    assert by["藻"].shape == "⿱艹澡(⿰氵喿(⿱品(∴口口口)木))"                       # nested, named composites
    assert by["器"].shape == "⁙口口犬口口" and by["器"].tree.pattern == "LU-RU-M-LD-RD"
    assert by["哭"].shape == "∵口口犬" and by["哭"].tree.pattern == "LU-RU-D"       # D, LU, RU put in reading order
    assert by["虹"].shape == "⿰虫工" and by["近"].shape == "⿺辶斤" and by["国"].shape == "⿴囗玉"
    assert [(p.c, p.pos) for p in by["器"].tree.parts] == [("口", "LU"), ("口", "RU"), ("犬", "M"), ("口", "LD"), ("口", "RD")]


def test_primitives_and_review_flags(raw_db):
    src = SqliteSource(raw_db)
    by = {e.char: e for e in src.entries()}
    assert by["半"].tree.is_leaf and "no decomposition" in by["半"].note
    assert "Mi" in by["咸"].review and by["咸"].shape == "<M-Mi>戌口"
    assert [c for c, _ in src.report.to_review] == ["咸"]


def test_rows_that_cannot_be_converted_are_left_out_not_guessed(raw_db):
    src = SqliteSource(raw_db)
    chars = {e.char for e in src.entries()}
    assert not chars & {"嗀", "单", "妈", "別"}
    reasons = {zi: r for zi, r, _ in src.report.quarantined}
    assert "more than one part" in reasons["嗀"] and "incomplete" in reasons["单"]
    assert "placeholder" in reasons["妈"] and "not active" in reasons["別"]


def test_a_cycle_ends_and_depth_limits_expansion(raw_db):
    by = {e.char: e for e in SqliteSource(raw_db).entries()}
    assert by["甲"].shape.count("甲") == 1                       # 甲 -> 乙 -> 甲 stops at the repeat
    shallow = {e.char: e for e in SqliteSource(raw_db, depth=1).entries()}
    assert shallow["藻"].shape == "⿱艹澡"                         # depth 1: one level only


def test_lexicon_from_the_database(raw_db, tmp_path):
    lex = SqliteSource(raw_db).lexicon()
    assert lex.get_pinyin("日") == "rì" and lex.get_gloss("日") == "sun"          # elemental table first
    assert lex.get_gloss("口") == "mouth" and lex.get_pinyin("犬") == "quǎn"       # tone numbers converted
    assert lex.get_pinyin("女") is None or lex.get_pinyin("女") == "nǚ"
    assert lex.get_gloss("氵") is None or lex.get_gloss("氵") == "water"
    mine = tmp_path / "mine.yaml"
    mine.write_text("日: {pinyin: rì, gloss: {en: day}}\n", encoding="utf-8")
    assert SqliteSource(raw_db).lexicon([mine]).get_gloss("日") == "day"              # a file replaces the database


def test_every_database_entry_passes_the_same_validator(raw_db):
    ws = [w for e in SqliteSource(raw_db).entries() for w in validate_entry(e)]
    assert [w.code for w in ws] == []                                                  # nothing to flag in this data


# ---- YAML is the intermediate form ---------------------------------------------------------------------

def test_extraction_round_trips_through_yaml_exactly(raw_db, tmp_path):
    src = SqliteSource(raw_db)
    path = tmp_path / "out.yaml"
    path.write_text(dump_entries(src.entry_dicts(), "# test"), encoding="utf-8")
    back = load_yaml(path)
    orig = src.entries()
    assert [e.char for e in back] == [e.char for e in orig]
    for a, b in zip(orig, back):
        assert (a.shape, a.pinyin, a.meaning, a.note, a.review) == (b.shape, b.pinyin, b.meaning, b.note, b.review)
        assert node_to_dict(a.tree) == node_to_dict(b.tree)


def test_dump_lexicon_is_valid_yaml(raw_db):
    import yaml
    d = yaml.safe_load(dump_lexicon(SqliteSource(raw_db).lexicon_dict()))
    assert d["日"]["gloss"]["en"] == "sun" and d["日"]["pinyin"] == "rì"


# ---- zx tables: a separate, derived copy --------------------------------------------------------------

def test_build_from_raw_reads_only_and_writes_a_separate_file(raw_db, tmp_path):
    before = _sha(raw_db)
    zx = zxdb.build_from_raw(raw_db)
    out = zxdb.write_zx(zx, tmp_path / "zitex.sqlite3")
    assert _sha(raw_db) == before                                                      # the source is untouched
    assert zxdb.has_zx(out) and not zxdb.has_raw(out) and zxdb.has_raw(raw_db) and not zxdb.has_zx(raw_db)
    con = sqlite3.connect(out)
    assert {r[0] for r in con.execute("select name from sqlite_master where type='table'")} == set(zxdb.ZX_TABLES)
    assert con.execute("select count(*) from zx_quarantine").fetchone()[0] == 4
    meta = dict(con.execute("select key, value from zx_meta"))
    assert meta["source_sha256"] == before and meta["source"] == "work.sqlite3"           # the file name, not a path
    con.close()


def test_the_zx_file_gives_the_same_entries_as_the_raw_tables(raw_db, tmp_path):
    out = zxdb.write_zx(zxdb.build_from_raw(raw_db), tmp_path / "zitex.sqlite3")
    from_raw, from_zx = SqliteSource(raw_db), SqliteSource(out)
    assert [(e.char, e.shape) for e in from_raw.entries()] == [(e.char, e.shape) for e in from_zx.entries()]
    assert from_raw.from_raw and not from_zx.from_raw
    assert from_raw.lexicon_dict() == from_zx.lexicon_dict()
    assert zxdb.write_zx(zxdb.build_from_raw(raw_db), out) == out                      # rebuilding replaces the tables


def test_refuses_to_write_into_a_database_that_has_other_tables(raw_db):
    with pytest.raises(ValueError, match="other tables"):
        zxdb.write_zx(zxdb.build_from_raw(raw_db), raw_db)
    assert not zxdb.has_zx(raw_db)


def test_in_place_makes_a_backup_first(raw_db):
    before = _sha(raw_db)
    zxdb.write_zx(zxdb.build_from_raw(raw_db), raw_db, in_place=True)
    backups = list(raw_db.parent.glob(raw_db.name + ".bak-*"))
    assert len(backups) == 1 and _sha(backups[0]) == before
    assert zxdb.has_zx(raw_db) and zxdb.has_raw(raw_db)


def test_opening_the_zx_file_or_the_raw_file_never_writes(raw_db, tmp_path):
    out = zxdb.write_zx(zxdb.build_from_raw(raw_db), tmp_path / "zitex.sqlite3")
    h1, h2 = _sha(raw_db), _sha(out)
    SqliteSource(raw_db).entries()
    SqliteSource(out).entries()
    assert (_sha(raw_db), _sha(out)) == (h1, h2)


def test_an_unrelated_database_is_an_error(tmp_path):
    p = tmp_path / "other.sqlite3"
    sqlite3.connect(p).execute("create table x (a)").connection.commit()
    with pytest.raises(ValueError, match="neither"):
        SqliteSource(p).entries()


# ---- the commands ----------------------------------------------------------------------------------------

def _run(args, cwd):
    import os
    old = os.getcwd()
    os.chdir(cwd)
    try:
        return CliRunner().invoke(main, args)
    finally:
        os.chdir(old)


def test_db_build_default_output_and_report(raw_db, tmp_path):
    r = _run(["db-build", "-i", str(raw_db), "--report", str(tmp_path / "q.csv")], tmp_path)
    assert r.exit_code == 0, r.output
    assert (raw_db.parent / "zitex.sqlite3").exists() and "source unchanged" in r.output
    assert (tmp_path / "q.csv").read_text(encoding="utf-8").startswith("zi,reason,cells")
    assert "more than one part" in r.output and "neither elemental nor decomposed" in r.output
    assert (tmp_path / "q-undecomposed.csv").read_text(encoding="utf-8").startswith("zi,used_as_a_part_n_times")


def test_db_build_will_not_write_into_the_source_without_in_place(raw_db, tmp_path):
    before = _sha(raw_db)
    r = _run(["db-build", "-i", str(raw_db), "-o", str(raw_db)], tmp_path)
    assert r.exit_code == 2 and "--in-place" in r.output and _sha(raw_db) == before
    assert _run(["db-build", "-i", str(raw_db), "--in-place"], tmp_path).exit_code == 0
    assert zxdb.has_zx(raw_db) and list(raw_db.parent.glob("*.bak-*"))


def test_db_build_needs_a_working_database(tmp_path):
    r = _run(["db-build", "-i", str(DATA / "chars.yaml")], tmp_path)
    assert r.exit_code == 2


def test_extract_fills_a_folder_and_will_not_overwrite(raw_db, tmp_path):
    r = _run(["extract", "-i", str(raw_db), "-c", "時,器", "-o", "work"], tmp_path)
    assert r.exit_code == 0, r.output
    names = {p.name for p in (tmp_path / "work").iterdir()}
    assert {"chars.yaml", "lexicon.yaml", "main.tex", "zitex-out"} <= names and "db-chars.yaml" not in names   # no db- prefix
    assert [e.char for e in load_yaml(tmp_path / "work" / "chars.yaml")] == ["時", "器"]                   # in the order named
    assert "日" in (tmp_path / "work" / "lexicon.yaml").read_text(encoding="utf-8")
    (tmp_path / "work" / "main.tex").write_text("old\n", encoding="utf-8")
    assert _run(["extract", "-i", str(raw_db), "-c", "時", "-o", "work"], tmp_path).exit_code == 0        # a re-run overwrites
    assert [e.char for e in load_yaml(tmp_path / "work" / "chars.yaml")] == ["時"]
    assert (tmp_path / "work" / "main.tex").read_text(encoding="utf-8") != "old\n"
    assert _run(["extract", "-i", str(raw_db), "-o", "work", "--force"], tmp_path).exit_code == 2          # the flag is gone
    assert _run(["extract", "-i", str(DATA / "chars.yaml"), "-o", "w2"], tmp_path).exit_code == 2             # YAML has nothing to extract


def test_check_shape_patterns_and_render_accept_a_database(raw_db, tmp_path):
    assert "entries" in _run(["check", "-i", str(raw_db)], tmp_path).output
    shape = _run(["shape", "-i", str(raw_db)], tmp_path).output
    assert "器\t⁙口口犬口口" in shape
    pat = _run(["patterns", "-i", str(raw_db)], tmp_path).output
    assert "L-M" in pat and "LU-RU-M-LD-RD" in pat and "⁙" in pat
    assert "levels" in _run(["patterns", "-i", str(raw_db), "--all-levels"], tmp_path).output
    r = _run(["render", "-i", str(raw_db), "-c", "時", "-s", "math", "-o", "-"], tmp_path)
    assert r.exit_code == 0 and r"_{\text{sun}}" in r.output and r"\overset{\text{shí}}" in r.output   # glosses from the DB


def test_render_a_database_into_a_directory(raw_db, tmp_path):
    r = _run(["render", "-i", str(raw_db), "-c", "器,哭", "-s", "tree", "--emit", "tex", "-o", "o/"], tmp_path)
    assert r.exit_code == 0, r.output
    assert sorted(p.name for p in (tmp_path / "o").iterdir()) == ["哭-tree.tex", "器-tree.tex"]


def test_a_local_lexicon_yaml_overrides_the_database(raw_db, tmp_path):
    (tmp_path / "lexicon.yaml").write_text("日: {pinyin: rì, gloss: {en: day}}\n", encoding="utf-8")
    r = _run(["render", "-i", str(raw_db), "-c", "時", "-s", "math", "-o", "-"], tmp_path)
    assert r"_{\text{day}}" in r.output


# ---- the real database, when it is there ---------------------------------------------------------------------

@pytest.mark.skipif(not REAL_DB.exists(), reason="no real database: set ZITEX_REAL_DB to run this test")
def test_real_database_is_read_only_and_converts():
    before = _sha(REAL_DB)
    src = SqliteSource(REAL_DB)
    entries = src.entries()
    assert _sha(REAL_DB) == before                                       # opening and converting never writes
    assert len(entries) > 5000 and src.from_raw
    top, _ = src.report.patterns.most_common(1)[0]
    assert top == "L-M" and src.report.patterns["L-M"] > 2500
    assert len(src.report.quarantined) < 500                             # a few hundred rows are left out, not most


def test_gloss_helpers():
    from zitex.zxdb import meaning_text, short_gloss
    assert short_gloss("(bound form) up;  upper") == "up" and meaning_text("(bound form) up;  upper") == "up; upper"
    assert short_gloss("device/tool/utensil/CL:臺|台[tai2]") == "device"                  # classifier cross-reference dropped
    assert short_gloss("Buddha;  Buddhism (abbr. for 佛陀[Fo2 tuo2]);  seemingly") == "Buddha"
    assert short_gloss("used in 舾裝|舾装[xi1 zhuang1]") is None and short_gloss(None) is None and short_gloss("") is None
    assert meaning_text("to swim (bound form)") == "to swim"
    assert meaning_text("a/b/c/d/e") == "a; b; c"                                          # at most three senses


# ---- attribution: CEDICT-derived data carries its licence with it ----------------------------------------

def test_attribution_is_stored_in_the_database_file(raw_db, tmp_path):
    out = zxdb.write_zx(zxdb.build_from_raw(raw_db), tmp_path / "zitex.sqlite3")
    meta = dict(sqlite3.connect(out).execute("select key, value from zx_meta"))
    assert "CC-CEDICT" in meta["attribution"] and "CC BY-SA 4.0" in meta["attribution"] and "Changes:" in meta["attribution"]
    src = SqliteSource(out)
    src.entries()                                                    # the metadata is read with the data
    assert src.report.meta["attribution"] == meta["attribution"]


def test_extract_writes_the_attribution_at_the_top(raw_db, tmp_path):
    r = _run(["extract", "-i", str(raw_db), "-c", "時"], tmp_path)
    assert r.exit_code == 0, r.output
    for name in ("chars.yaml", "lexicon.yaml"):
        head = (tmp_path / name).read_text(encoding="utf-8").split("\n\n")[0]
        assert "CC-CEDICT" in head and "CC BY-SA 4.0" in head and head.startswith("# Generated by zitex")
    assert load_yaml(tmp_path / "chars.yaml")[0].char == "時"                        # the header is only comments


def test_the_repository_carries_the_notice():
    root = Path(__file__).parent.parent
    notice = (root / "db" / "NOTICE.md").read_text(encoding="utf-8")
    assert "CC-CEDICT" in notice and "CC BY-SA 4.0" in notice and "Changes made" in notice
    assert "CC-CEDICT" in (root / "README.md").read_text(encoding="utf-8")
    if (root / "db" / "zitex.sqlite3").exists():
        assert "CC-CEDICT" in dict(sqlite3.connect(root / "db" / "zitex.sqlite3").execute("select key, value from zx_meta"))["attribution"]


def test_extracted_files_go_straight_into_render(raw_db, tmp_path):
    """The point of `extract`: its two files are what the ordinary render command reads."""
    assert _run(["extract", "-i", str(raw_db), "-c", "時,器"], tmp_path).exit_code == 0
    r = _run(["render", "-i", "chars.yaml", "-c", "器", "-s", "math", "-o", "-"], tmp_path)           # lexicon.yaml is picked up by default
    assert r.exit_code == 0 and r"_{\text{mouth}}" in r.output and r"\overset{\text{kǒu}}" in r.output
    direct = _run(["render", "-i", str(raw_db), "-c", "器", "-s", "math", "-o", "-"], tmp_path).output
    # extracting and then rendering equals rendering directly (the raw source adds a note on stderr first)
    assert direct.splitlines()[-1] == r.output.splitlines()[-1]


# ---- revisions: corrections made by hand ----------------------------------------------------------------------------

@pytest.fixture
def zx_file(raw_db, tmp_path):
    return zxdb.write_zx(zxdb.build_from_raw(raw_db), tmp_path / "zitex.sqlite3")


def _shapes(path):
    return {e.char: e.shape for e in SqliteSource(path).entries()}


def test_revise_changes_the_character_and_everything_built_on_it(zx_file):
    assert _shapes(zx_file)["藻"] == "⿱艹澡(⿰氵喿(⿱品(∴口口口)木))"
    ordered = zxdb.revise(zx_file, "品", [("RD", "木"), ("U", "口"), ("LD", "口")], note="test")
    assert ordered == [("U", "口"), ("LD", "口"), ("RD", "木")]                      # stored in reading order
    s = _shapes(zx_file)
    assert s["品"] == "∴口口木" and "∴口口木" in s["藻"]                              # the change shows in 藻 as well


def test_a_character_can_be_made_a_primitive(zx_file):
    zxdb.revise(zx_file, "寺", [])
    s = _shapes(zx_file)
    assert s["寺"] == "寺" and s["時"] == "⿰日寺"
    by = {e.char: e for e in SqliteSource(zx_file).entries()}
    assert by["寺"].tree.is_leaf


def test_revise_checks_what_it_is_given(zx_file):
    for bad in ([("L", "日")], [("L", "日"), ("X", "月")], [("L", "日月"), ("R", "月")], [("L", "?"), ("R", "月")]):
        with pytest.raises(ValueError):
            zxdb.revise(zx_file, "時", bad)
    assert _shapes(zx_file)["時"] == "⿰日寺"                                         # nothing changed


def test_revert_puts_back_the_original(zx_file):
    before = _shapes(zx_file)
    zxdb.revise(zx_file, "時", [("L", "月"), ("M", "寺")])
    zxdb.revise(zx_file, "時", [("U", "日"), ("D", "寺")])                           # revised twice
    assert _shapes(zx_file)["時"] == "⿱日寺"
    assert [r["zi"] for r in zxdb.list_revisions(zx_file)] == ["時"]
    assert zxdb.revert(zx_file, "時") is True
    assert _shapes(zx_file) == before and zxdb.list_revisions(zx_file) == []
    assert zxdb.revert(zx_file, "時") is False                                       # nothing left to undo


def test_a_left_out_row_can_be_revised_and_reverted(zx_file):
    assert "嗀" not in _shapes(zx_file)
    zxdb.revise(zx_file, "嗀", [("L", "冖"), ("M", "一"), ("R", "殳")], note="fixed the two parts in one cell")
    assert _shapes(zx_file)["嗀"]
    con = sqlite3.connect(zx_file)
    assert con.execute("select count(*) from zx_quarantine where zi='嗀'").fetchone()[0] == 0
    con.close()
    zxdb.revert(zx_file, "嗀")
    assert "嗀" not in _shapes(zx_file)
    con = sqlite3.connect(zx_file)
    assert con.execute("select reason from zx_quarantine where zi='嗀'").fetchone()[0].startswith("a position holds")
    con.close()


def test_revisions_survive_a_rebuild(raw_db, zx_file):
    zxdb.revise(zx_file, "寺", [], note="kept whole")
    zxdb.revise(zx_file, "嗀", [("L", "冖"), ("R", "殳")])
    zxdb.write_zx(zxdb.build_from_raw(raw_db), zx_file)                              # `zitex db-build` again
    s = _shapes(zx_file)
    assert s["寺"] == "寺" and s["嗀"]
    assert {r["zi"] for r in zxdb.list_revisions(zx_file)} == {"寺", "嗀"}
    assert dict(sqlite3.connect(zx_file).execute("select key, value from zx_meta"))["revisions_reapplied"] == "2"
    assert zxdb.revert(zx_file, "寺") and _shapes(zx_file)["寺"] == "⿱土寸"            # "original" is the freshly built row


def test_revise_will_not_touch_a_database_without_zx_tables(raw_db):
    before = _sha(raw_db)
    with pytest.raises(ValueError, match="db-build"):
        zxdb.revise(raw_db, "時", [("L", "月"), ("R", "寺")])
    assert _sha(raw_db) == before


def test_an_older_zx_file_without_the_revision_table_still_works(zx_file):
    con = sqlite3.connect(zx_file)
    con.execute("drop table zx_revision")
    con.commit()
    con.close()
    assert zxdb.has_zx(zx_file) and zxdb.list_revisions(zx_file) == []
    zxdb.revise(zx_file, "寺", [])                                                   # the table is created when needed
    assert [r["zi"] for r in zxdb.list_revisions(zx_file)] == ["寺"]


def test_db_build_says_how_many_revisions_it_re_applied(raw_db, tmp_path):
    out = tmp_path / "zitex.sqlite3"
    assert _run(["db-build", "-i", str(raw_db), "-o", str(out)], tmp_path).exit_code == 0
    zxdb.revise(out, "寺", [])
    r = _run(["db-build", "-i", str(raw_db), "-o", str(out)], tmp_path)
    assert r.exit_code == 0 and "re-applied 1 revision" in r.output and _shapes(out)["寺"] == "寺"


def test_a_revision_can_make_a_character_elemental_and_revert_restores_the_flag(zx_file):
    def flags(zi):
        con = sqlite3.connect(zx_file)
        try:
            return con.execute("select is_elemental, has_parts from zx_char where zi=?", (zi,)).fetchone()
        finally:
            con.close()
    assert flags("藻") == (0, 1)
    zxdb.revise(zx_file, "藻", [], note="a primitive", elemental=True)
    assert flags("藻") == (1, 0)
    assert zxdb.list_revisions(zx_file)[0]["elemental"] is True
    assert zxdb.revert(zx_file, "藻") and flags("藻") == (0, 1)               # the flag goes back too
    zxdb.revise(zx_file, "藻", [("U", "艹"), ("D", "澡")])                      # elemental=None leaves the flag alone
    assert flags("藻") == (0, 1) and zxdb.list_revisions(zx_file)[0]["elemental"] is None


def test_an_elemental_character_is_not_expanded_inside_others(zx_file):
    assert _shapes(zx_file)["時"] == "⿰日寺"
    zxdb.revise(zx_file, "日", [("U", "一"), ("D", "口")], elemental=True)    # decomposed, but elemental: it stays whole in 時
    s = _shapes(zx_file)
    assert s["日"] == "⿱一口" and s["時"] == "⿰日寺"


def test_the_elemental_flag_and_the_revision_survive_a_rebuild(raw_db, zx_file):
    zxdb.revise(zx_file, "藻", [], note="primitive", elemental=True)
    zxdb.write_zx(zxdb.build_from_raw(raw_db), zx_file)
    con = sqlite3.connect(zx_file)
    assert con.execute("select is_elemental, has_parts from zx_char where zi='藻'").fetchone() == (1, 0)
    con.close()
    assert zxdb.list_revisions(zx_file)[0]["elemental"] is True


def test_db_build_reports_elemental_characters_that_still_have_a_decomposition(raw_db, tmp_path):
    # in the synthetic database 寺 and 日 are elemental; 寺 has a decomposition row, 日 has none
    r = _run(["db-build", "-i", str(raw_db), "-o", str(tmp_path / "z.sqlite3"), "--report", str(tmp_path / "q.csv")], tmp_path)
    assert r.exit_code == 0, r.output
    assert "elemental characters still have a decomposition" in r.output
    rows = (tmp_path / "q-elemental-decomposed.csv").read_text(encoding="utf-8").splitlines()
    assert rows[0] == "zi,decomposition" and any(line.startswith("寺,") for line in rows)
