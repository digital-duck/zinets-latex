from pathlib import Path

import pytest

from zitex import (OPS, ParseError, load_yaml, node_from_dict, node_to_dict,
                        parse_ids, to_ids, validate_entry)

DATA = Path(__file__).parent / "data" / "chars.yaml"


@pytest.fixture(scope="module")
def entries():
    return load_yaml(DATA)


def test_loads_all(entries):
    assert len(entries) == 23


def test_ids_matches_tree_and_no_warnings(entries):
    for e in entries:
        assert validate_entry(e) == [], e.char


def test_ids_roundtrip(entries):
    for e in entries:
        assert to_ids(parse_ids(e.ids)) == e.ids, e.char


def test_expansion_equals_stored_tree(entries):
    # the compact form expands to the same tree (incl. positions) as the stored one
    for e in entries:
        assert node_to_dict(parse_ids(e.ids)) == node_to_dict(e.tree), e.char


def test_dict_roundtrip(entries):
    for e in entries:
        assert node_to_dict(node_from_dict(node_to_dict(e.tree))) == node_to_dict(e.tree)


def test_triangle_ops():
    n = parse_ids("∴口口口")
    assert [p.pos for p in n.parts] == ["上", "左下", "右下"]
    n = parse_ids("∵口口犬")
    assert [(p.c, p.pos) for p in n.parts] == [("口", "左上"), ("口", "右上"), ("犬", "下")]


def test_named_group():
    n = parse_ids("⿱艹⿰氵喿(⿱品(∴口口口)木)")
    zao = n.parts[1].parts[1]
    assert zao.c == "喿" and zao.op == "⿱" and zao.pos == "右"
    assert zao.parts[0].c == "品" and zao.parts[0].op == "∴"


@pytest.mark.parametrize("bad", ["", "⿰日", "⿰日寺口", "(日)", "日(寺)", "⿱艹⿰氵", "∴口口"])
def test_parse_errors(bad):
    with pytest.raises(ParseError):
        parse_ids(bad)


def test_every_op_has_default_positions():
    assert len(OPS) == 14
    assert all(len(v) in (2, 3) for v in OPS.values())


def test_warnings():
    from zitex.loader import entry_from_dict
    e = entry_from_dict({"char": "X", "ids": "⿰日寺",
                         "tree": {"op": "⿰", "parts": [{"c": "日", "pos": "上"}, {"c": "寺"}]}})
    codes = sorted(w.code for w in validate_entry(e))
    assert codes == ["W2", "W3"]
    e = entry_from_dict({"char": "Y", "tree": {"op": "⿰", "parts": [{"c": "日", "pos": "foo"}]}})
    codes = sorted(w.code for w in validate_entry(e))
    assert codes == ["W1", "W5"]
    e = entry_from_dict({"char": "Z", "ids": "⿱日寺", "tree": {"op": "⿰", "parts": [{"c": "日", "pos": "左"}, {"c": "寺", "pos": "右"}]}})
    assert [w.code for w in validate_entry(e)] == ["W4"]
