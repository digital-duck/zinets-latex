import shutil
from pathlib import Path

import pytest

from zitex import zxdb
from zitex.pipeline import _skipped, generate_pdf, parse_chars, pdf_to_pngs
from zitex.workspace import MAX_CHARS

needs_xelatex = pytest.mark.skipif(shutil.which("xelatex") is None, reason="xelatex not installed")


@pytest.fixture
def zx_db(raw_db, tmp_path):
    (tmp_path / "built").mkdir()
    return zxdb.write_zx(zxdb.build_from_raw(raw_db), tmp_path / "built" / "zitex.sqlite3")


def test_parse_chars():
    assert parse_chars("器,藻 佛") == ["器", "藻", "佛"]
    assert parse_chars("器，藻、佛\n時") == ["器", "藻", "佛", "時"]
    assert parse_chars("器,器,藻") == ["器", "藻"] and parse_chars("") == [] and parse_chars(" , ") == []


def test_parse_chars_splits_a_phrase_without_delimiters():
    assert parse_chars("守株待兔") == ["守", "株", "待", "兔"]
    assert parse_chars("守株待兔，守株待兔。") == ["守", "株", "待", "兔"]          # repeats once, punctuation skipped
    assert parse_chars("器藻 佛,時") == ["器", "藻", "佛", "時"]                   # mixed with delimiters
    assert parse_chars("𠀉口") == ["𠀉", "口"]                                       # characters outside the basic plane


def test_skipped_reads_extract_output():
    assert _skipped("not in /x/zitex.sqlite3: 龘 也\nwrote a") == ["龘", "也"]
    assert _skipped("wrote chars.yaml: 2 characters") == []


def test_nothing_to_do_without_characters(zx_db, tmp_path):
    r = generate_pdf(" , ", zx_db, tmp_path / "w")
    assert not r.ok and r.message and r.steps == []


def test_extract_failure_stops_the_run_and_says_why(zx_db, tmp_path):
    r = generate_pdf("龘", zx_db, tmp_path / "w")
    assert not r.ok and [s.name for s in r.steps] == ["setup", "extract"] and "extract failed" in r.message
    assert r.missing == ["龘"] and r.pdf is None


def test_a_bad_database_fails_in_extract(tmp_path):
    r = generate_pdf("器", tmp_path / "nope.sqlite3", tmp_path / "w")
    assert not r.ok and r.steps[-1].name == "extract" and not r.steps[-1].ok


def test_the_cap_is_applied_before_extract(zx_db, tmp_path, monkeypatch):
    import zitex.pipeline as pipeline
    monkeypatch.setattr(pipeline, "MAX_CHARS", 2)
    seen = []
    r = generate_pdf("器,時,藻", zx_db, tmp_path / "w", on_step=seen.append)
    assert r.chars == ["器", "時"] and r.truncated == 1
    assert "器,時" in " ".join(seen[1].command) and "藻" not in " ".join(seen[1].command)
    assert MAX_CHARS == 60


@needs_xelatex
def test_the_whole_flow_makes_a_pdf_and_reports_an_unknown_character(zx_db, tmp_path):
    steps = []
    r = generate_pdf("器,時,龘", zx_db, tmp_path / "work", on_step=steps.append)
    assert r.ok and r.pdf == tmp_path / "work" / "main.pdf" and r.pdf.stat().st_size > 1000
    assert [s.name for s in r.steps] == ["setup", "extract", "xelatex"] and [s.name for s in steps] == ["setup", "extract", "xelatex"]
    assert r.missing == ["龘"] and "$ " in r.log
    assert {"chars.yaml", "lexicon.yaml", "main.tex", "zitex.sty", "fonts.yaml"} <= {p.name for p in (tmp_path / "work").iterdir()}
    again = generate_pdf("時", zx_db, tmp_path / "work")                 # the folder is reused: --force, and a fresh PDF
    assert again.ok and again.chars == ["時"]
    if shutil.which("pdftoppm"):
        assert len(pdf_to_pngs(again.pdf, tmp_path / "png")) >= 1
