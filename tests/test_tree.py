from pathlib import Path

import pytest

from zitex import (OPS, ParseError, load_yaml, node_from_dict, node_to_dict,
                        parse_shape, to_shape, validate_entry)

DATA = Path(__file__).parent / "data" / "chars.yaml"


@pytest.fixture(scope="module")
def entries():
    return load_yaml(DATA)


def test_loads_all(entries):
    assert len(entries) == 29


def test_shape_matches_tree_and_no_warnings(entries):
    for e in entries:
        assert validate_entry(e) == [], e.char


def test_shape_roundtrip(entries):
    for e in entries:
        assert to_shape(parse_shape(e.shape)) == e.shape, e.char


def test_expansion_equals_stored_tree(entries):
    # the compact form expands to the same tree (incl. positions) as the stored one
    for e in entries:
        assert node_to_dict(parse_shape(e.shape)) == node_to_dict(e.tree), e.char


def test_dict_roundtrip(entries):
    for e in entries:
        assert node_to_dict(node_from_dict(node_to_dict(e.tree))) == node_to_dict(e.tree)


def test_flat_operators():
    n = parse_shape("∴口口口")
    assert [p.pos for p in n.parts] == ["U", "LD", "RD"] and n.pattern == "U-LD-RD"
    n = parse_shape("∵口口犬")
    assert [(p.c, p.pos) for p in n.parts] == [("口", "LU"), ("口", "RU"), ("犬", "D")]
    assert parse_shape("∷又又又又").pattern == "LU-RU-LD-RD"
    assert parse_shape("⁙口口犬口口").pattern == "LU-RU-M-LD-RD"


def test_general_pattern_operator():
    n = parse_shape("<L-RU-RD>又又又")
    assert n.op == "<L-RU-RD>" and [p.pos for p in n.parts] == ["L", "RU", "RD"]
    assert to_shape(n) == "<L-RU-RD>又又又"
    assert parse_shape("<LU-LD-R>木木木").pattern == "LU-LD-R"
    # the same level through the symbol and through the general form has the same pattern
    assert parse_shape("<LU-RU-M-LD-RD>口口犬口口").pattern == parse_shape("⁙口口犬口口").pattern


@pytest.mark.parametrize("bad", ["<>口", "<L-R", "<L-XX>日月", "<L-R>日"])
def test_general_pattern_errors(bad):
    with pytest.raises(ParseError):
        parse_shape(bad)


def test_radical_rule_sets_defaults():
    # a radical is peripheral, the other part is M; two radicals or none are peers
    assert parse_shape("⿰日寺").pattern == "L-M"      # 日 radical
    assert parse_shape("⿰亻弗").pattern == "L-M"      # 亻 variant radical
    assert parse_shape("⿰弗刂").pattern == "M-R"      # 刂 radical on the right
    assert parse_shape("⿱艹澡").pattern == "U-M"
    assert parse_shape("⿱相心").pattern == "M-D"
    assert parse_shape("⿰又又").pattern == "L-R"      # both radicals
    assert parse_shape("⿰弗弗").pattern == "L-R"      # neither


def test_enclosure_patterns():
    assert parse_shape("⿴囗或").pattern == "Mo-M"
    assert parse_shape("⿵冂口").pattern == "Mo-D"
    assert parse_shape("⿶凵口").pattern == "Mo-U"
    assert parse_shape("⿷匚乂").pattern == "Mo-R"
    assert parse_shape("⿸疒丙").pattern == "LU-M" and parse_shape("⿺辶斤").pattern == "LD-M"
    assert parse_shape("⿲彳氵亍").pattern == "L-M-R" and parse_shape("⿳爫冖心").pattern == "U-M-D"


def test_chinese_position_labels_are_accepted_as_input():
    n = node_from_dict({"op": "⿰", "parts": [{"c": "日", "pos": "左"}, {"c": "寺", "pos": "中"}]})
    assert n.pattern == "L-M"
    n = node_from_dict({"op": "⿴", "parts": [{"c": "囗", "pos": "中外"}, {"c": "或", "pos": "中"}]})
    assert n.pattern == "Mo-M"


def test_five_part_pattern_from_the_author_db():
    n = parse_shape("⁙口口犬口口")
    assert [(p.c, p.pos) for p in n.parts] == [("口", "LU"), ("口", "RU"), ("犬", "M"), ("口", "LD"), ("口", "RD")]


def test_named_group():
    n = parse_shape("⿱艹⿰氵喿(⿱品(∴口口口)木)")
    zao = n.parts[1].parts[1]
    assert zao.c == "喿" and zao.op == "⿱" and zao.pos == "M"
    assert zao.parts[0].c == "品" and zao.parts[0].op == "∴"


@pytest.mark.parametrize("bad", ["", "⿰日", "⿰日寺口", "(日)", "日(寺)", "⿱艹⿰氵", "∴口口"])
def test_parse_errors(bad):
    with pytest.raises(ParseError):
        parse_shape(bad)


def test_operator_table():
    from zitex.ops import POSITIONS, allowed, arity
    assert len(OPS) == 16 and len(POSITIONS) == 11
    for op, pats in OPS.items():
        assert all(len(p) == arity(op) for p in pats), op
        assert all(x in POSITIONS for p in pats for x in p), op


def _codes(d):
    from zitex.loader import entry_from_dict
    return sorted(w.code for w in validate_entry(entry_from_dict(d)))


def test_warnings():
    # W3 missing pos; the other pos fits no allowed pattern for ⿰ (U-?), reported as W3 only (a label is missing)
    assert _codes({"char": "X", "tree": {"op": "⿰", "parts": [{"c": "日", "pos": "U"}, {"c": "寺"}]}}) == ["W3"]
    # W2 pattern not allowed for the operator
    assert _codes({"char": "X", "tree": {"op": "⿰", "parts": [{"c": "日", "pos": "U"}, {"c": "寺", "pos": "D"}]}}) == ["W2"]
    # W1 unknown label, W5 wrong number of children
    assert _codes({"char": "Y", "tree": {"op": "⿰", "parts": [{"c": "日", "pos": "foo"}]}}) == ["W1", "W5"]
    # W4 shape differs from the tree
    assert _codes({"char": "Z", "shape": "⿱日寺", "tree": {"op": "⿰", "parts": [{"c": "日", "pos": "L"}, {"c": "寺", "pos": "M"}]}}) == ["W4"]
    # W6 empty branch
    assert _codes({"char": "E", "tree": {"op": "⿰", "parts": []}}) == ["W5", "W6"]


def test_w7_regions_overlap_and_alias():
    t = {"op": "∴", "parts": [{"c": "又", "pos": "U"}, {"c": "又", "pos": "L"}, {"c": "又", "pos": "R"}]}
    from zitex.loader import entry_from_dict
    ws = validate_entry(entry_from_dict({"char": "叒", "tree": t}))
    assert [w.code for w in ws] == ["W7"] and "U-LD-RD" in ws[0].msg      # U-L-R is allowed for ∴ but overlaps
    two_m = {"op": "⿰", "parts": [{"c": "日", "pos": "M"}, {"c": "寺", "pos": "M"}]}
    assert "W7" in _codes({"char": "X", "tree": two_m})


def test_w8_radical_labelled_m():
    # 日 is a radical and 寺 is not, so 日 should be peripheral
    bad = {"op": "⿰", "parts": [{"c": "日", "pos": "M"}, {"c": "寺", "pos": "R"}]}
    assert _codes({"char": "時", "tree": bad}) == ["W8"]
    ok = {"op": "⿰", "parts": [{"c": "日", "pos": "L"}, {"c": "寺", "pos": "M"}]}
    assert _codes({"char": "時", "tree": ok}) == []
    peers = {"op": "⿰", "parts": [{"c": "又", "pos": "L"}, {"c": "又", "pos": "R"}]}
    assert _codes({"char": "双", "tree": peers}) == []


def test_general_pattern_validates():
    t = {"op": "<L-RU-RD>", "parts": [{"c": "又", "pos": "L"}, {"c": "又", "pos": "RU"}, {"c": "又", "pos": "RD"}]}
    assert _codes({"char": "X", "tree": t}) == []
    t["parts"][1]["pos"] = "R"      # L-R-RD overlaps and is not the pattern of the operator
    assert "W2" in _codes({"char": "X", "tree": t})


def test_old_ids_key_is_not_accepted():
    from zitex import ParseError
    from zitex.loader import entry_from_dict
    with pytest.raises(ParseError, match="shape"):
        entry_from_dict({"char": "好", "ids": "⿰女子"})


# ---- reading order and pattern -> operator (database input) -----------------------------------------------

@pytest.mark.parametrize("given,canonical", [
    ("D-LU-RU", "LU-RU-D"), ("LU-D-RU", "LU-RU-D"), ("LD-U-RD", "U-LD-RD"), ("LU-LD-R", "LU-LD-R"),
    ("L-RU-RD", "L-RU-RD"), ("M-Mo", "Mo-M"), ("L-U-R", "U-L-R"), ("LU-L-LD-R", "LU-L-LD-R"),
    ("LU-LD-M-RU-RD", "LU-RU-M-LD-RD"), ("M-L", "L-M"), ("R-M", "M-R"), ("D-U", "U-D"), ("D-M", "M-D"),
    ("M-U", "U-M"), ("M-LU", "LU-M"), ("D-M-U", "U-M-D"), ("R-M-L", "L-M-R"), ("Mi-M", "M-Mi"),
    ("LU-RU-LD-RD", "LU-RU-LD-RD"), ("RD-LD-RU-LU", "LU-RU-LD-RD"),
])
def test_reading_order(given, canonical):
    from zitex.ops import reading_order
    assert "-".join(reading_order(given.split("-"))) == canonical


def test_the_order_does_not_depend_on_the_order_given():
    import itertools
    from zitex.ops import reading_order
    for pat in ("LU-RU-M-LD-RD", "U-LD-RD", "LU-LD-R", "L-M-R"):
        labels = pat.split("-")
        assert {reading_order(p) for p in itertools.permutations(labels)} == {tuple(labels)}


@pytest.mark.parametrize("pattern,op", [
    ("L-M", "⿰"), ("M-R", "⿰"), ("U-D", "⿱"), ("L-M-R", "⿲"), ("U-M-D", "⿳"), ("LU-M", "⿸"), ("LD-M", "⿺"),
    ("Mo-M", "⿴"), ("Mo-D", "⿵"), ("Mo-U", "⿶"), ("Mo-R", "⿷"), ("U-LD-RD", "∴"), ("LU-RU-D", "∵"),
    ("LU-RU-LD-RD", "∷"), ("LU-RU-M-LD-RD", "⁙"),
    ("LU-LD-R", "<LU-LD-R>"), ("M-Mi", "<M-Mi>"), ("L-RU-RD", "<L-RU-RD>"),     # no operator allows these
])
def test_op_for_pattern(pattern, op):
    from zitex.ops import op_for_pattern
    assert op_for_pattern(pattern.split("-")) == op
    # a shape string gives back the same pattern, except that ⿰ and ⿱ choose theirs by the radical rule
    if op not in ("⿰", "⿱"):
        n = parse_shape(op + "".join("甲丙丁戊庚"[i] for i in range(len(pattern.split("-")))))
        assert n.pattern == pattern


def test_w7_understands_edge_middle_labels():
    # three parts across the top, or down the right: U / R mean the middle cell of that edge
    for shape in ("<LU-U-RU-D>日月木火", "<L-RU-R-RD>日月木火", "<LU-L-LD-R>日月木火", "∴又又又",
                  "<U-L-M-D>日月木火", "<U-L-R-D>日月木火"):
        assert _codes_of_shape(shape) == [], shape
    for shape in ("<U-L-R>又又又", "<L-U-R>日月木"):                       # U overlaps L and R in the corners
        assert _codes_of_shape(shape) == ["W7"], shape


def _codes_of_shape(shape):
    from zitex.loader import entry_from_dict
    return [w.code for w in validate_entry(entry_from_dict({"char": "X", "shape": shape}))]
