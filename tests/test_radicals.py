from zitex.radicals import KANGXI, SUPPLEMENT, VARIANTS, base_radical, is_radical, radical_number


def test_214_unique_radicals():
    assert len(KANGXI) == 214 and len(set(KANGXI)) == 214
    assert all(len(c) == 1 for c in KANGXI)


def test_numbering():
    assert KANGXI[0] == "一" and KANGXI[-1] == "龠"
    assert radical_number("人") == 9 and radical_number("心") == 61
    assert radical_number("日") == 72 and radical_number("水") == 85


def test_variants_map_to_a_kangxi_radical():
    assert all(base in KANGXI for base in VARIANTS.values())
    assert radical_number("亻") == 9 and radical_number("氵") == 85 and radical_number("忄") == 61
    assert base_radical("艹") == "艸" and base_radical("辶") == "辵"


def test_non_radicals():
    for ch in "寺弗每丙澡喿相":
        assert not is_radical(ch), ch
        assert radical_number(ch) is None


def test_zi_matrix_examples_from_the_paper():
    # 佛 亻(L) + 弗(M), 時 日(L) + 寺(M), 藻 艹(U) + 澡(M): the radical is the peripheral part
    for rad, body in [("亻", "弗"), ("日", "寺"), ("艹", "澡"), ("忄", "每"), ("疒", "丙")]:
        assert is_radical(rad) and not is_radical(body)


def test_supplement_block():
    assert "⺡" in SUPPLEMENT and is_radical("⺡")
    assert base_radical("⺡") == "水"        # CJK RADICAL WATER ONE
    assert base_radical("⺅") == "人"        # CJK RADICAL PERSON
