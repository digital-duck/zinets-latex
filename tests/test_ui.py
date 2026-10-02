"""The Streamlit pages, run headless with Streamlit's own test harness."""
import os
import shutil
from pathlib import Path

import pytest

st_testing = pytest.importorskip("streamlit.testing.v1")
AppTest = st_testing.AppTest

from zitex import zxdb  # noqa: E402
from zitex.sources import SqliteSource  # noqa: E402

UI = Path(__file__).parent.parent / "src" / "ui" / "streamlit"
needs_xelatex = pytest.mark.skipif(shutil.which("xelatex") is None, reason="xelatex not installed")


@pytest.fixture
def zx_db(raw_db, tmp_path):
    (tmp_path / "built").mkdir()
    return zxdb.write_zx(zxdb.build_from_raw(raw_db), tmp_path / "built" / "zitex.sqlite3")


def _app(page: str, db: Path) -> "AppTest":
    at = AppTest.from_file(str(UI / page), default_timeout=60)
    at.session_state["db"] = str(db)
    return at


def _texts(at):
    return " ".join(m.value for m in [*at.markdown, *at.subheader, *at.caption, *at.warning, *at.error, *at.success, *at.info])


# ---- home ---------------------------------------------------------------------------------------------------------

def test_home_page_runs(zx_db):
    at = _app("app.py", zx_db).run()
    assert not at.exception
    assert "zitex" in at.title[0].value and "Review decompositions" in _texts(at) and "Generate main.pdf" in _texts(at)


def test_the_app_lives_where_the_task_asked_for_it():
    assert (UI / "app.py").is_file() and (UI / "pages").is_dir()
    assert sorted(p.name for p in (UI / "pages").glob("*.py")) == ["1_Review_decompositions.py", "2_Generate_main_pdf.py"]
    assert not (UI / "__init__.py").exists()            # a package named streamlit would shadow the real one


# ---- page 1: review ------------------------------------------------------------------------------------------------

def test_review_page_shows_a_character(zx_db):
    at = _app("pages/1_Review_decompositions.py", zx_db)
    at.session_state["char"] = "時"
    at.run()
    assert not at.exception, at.exception
    text = _texts(at)
    assert "shí" in text and "Pattern **L-M**" in text
    assert any(c.value == "⿰日寺" for c in at.code)
    assert {m.label for m in at.metric} >= {"characters", "left out", "revised"}


def test_review_page_says_when_the_database_is_missing(tmp_path):
    at = _app("pages/1_Review_decompositions.py", tmp_path / "nope.sqlite3").run()
    assert not at.exception and any("No such file" in e.value for e in at.error)


def test_review_page_refuses_the_raw_working_database(raw_db):
    at = _app("pages/1_Review_decompositions.py", raw_db).run()
    assert not at.exception and any("raw working database" in w.value for w in at.warning)


def test_review_page_saves_and_reverts_a_revision(zx_db):
    at = _app("pages/1_Review_decompositions.py", zx_db)
    at.session_state["char"] = "寺"
    at.run()
    assert not at.exception, at.exception
    # an empty editor means a primitive: the same as the "no parts" revision
    notes = [t for t in at.text_input if t.label.startswith("Why")]
    notes[0].set_value("kept whole")
    save = next(b for b in at.button if b.label == "Save revision")
    save.click()
    at.run()
    assert not at.exception, at.exception
    # the editor still holds 土/寸, so saving writes them back unchanged: a revision exists, and the shape is the same
    assert [r["zi"] for r in zxdb.list_revisions(zx_db)] == ["寺"]
    revert = next(b for b in at.button if b.label == "Revert to the original")
    assert not revert.disabled
    revert.click()
    at.run()
    assert zxdb.list_revisions(zx_db) == []


def test_review_page_lists_what_to_review(zx_db):
    at = _app("pages/1_Review_decompositions.py", zx_db).run()
    assert not at.exception
    sel = next(s for s in at.selectbox if s.label == "List")
    assert any("Left out" in o for o in sel.options)
    sel.select("quarantine").run()
    assert not at.exception and any(len(d.value) for d in at.dataframe)


# ---- page 2: generate ---------------------------------------------------------------------------------------------

def test_generate_page_runs_and_reads_the_character_list(zx_db):
    at = _app("pages/2_Generate_main_pdf.py", zx_db).run()
    assert not at.exception
    area = at.text_area[0]
    assert area.value == "器,藻,佛" or area.value
    area.set_value("器 時，藻").run()
    assert any("3 characters" in c.value for c in at.caption)


@needs_xelatex
def test_generate_page_makes_a_pdf(zx_db, tmp_path, monkeypatch):
    import sys
    sys.path.insert(0, str(UI))
    import common
    monkeypatch.setattr(common, "WORKSPACE", tmp_path / "workspace")           # not the real workspace folder
    at = _app("pages/2_Generate_main_pdf.py", zx_db)
    at.run()
    at.text_area[0].set_value("器,時")
    at.run()
    next(b for b in at.button if b.label == "Generate main.pdf").click()
    at.run(timeout=180)
    assert not at.exception, at.exception
    assert (tmp_path / "workspace" / "main.pdf").exists()
    assert any("main.pdf" in s.value for s in at.success)


def test_review_page_takes_characters_outside_the_basic_plane(zx_db):
    """A character such as 𠂉 (U+20089) is one character, though a browser counts two UTF-16 units for it."""
    at = _app("pages/1_Review_decompositions.py", zx_db)
    at.session_state["char"] = "\U00020089"
    at.run()
    assert not at.exception and "is not in this database" in _texts(at)
    at.text_input[0].set_value("時陀").run()                                  # more than one: the first one is used
    assert not at.exception and any(c.value == "⿰日寺" for c in at.code)


@needs_xelatex
def test_generate_page_names_the_characters_it_left_out(zx_db, tmp_path, monkeypatch):
    import sys
    sys.path.insert(0, str(UI))
    import common
    monkeypatch.setattr(common, "WORKSPACE", tmp_path / "workspace")
    at = _app("pages/2_Generate_main_pdf.py", zx_db)
    at.run()
    at.text_area[0].set_value("器,龘")
    at.run()
    next(b for b in at.button if b.label == "Generate main.pdf").click()
    at.run(timeout=180)
    assert not at.exception, at.exception
    assert any("Not in the database, so left out: 龘" in w.value for w in at.warning)
    assert (tmp_path / "workspace" / "main.pdf").exists()
