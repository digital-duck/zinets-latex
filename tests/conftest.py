import sqlite3
from pathlib import Path

import pytest

COLS = ["zi_left_up", "zi_left", "zi_left_down", "zi_up", "zi_mid", "zi_down", "zi_right_up", "zi_right",
        "zi_right_down", "zi_mid_out", "zi_mid_in"]


def _row(zi, active="Y", **cells):
    return (zi, active, *[cells.get(c) for c in COLS])


@pytest.fixture
def raw_db(tmp_path) -> Path:
    """A small database shaped like the ZiNets working database (the tables and columns zitex reads)."""
    path = tmp_path / "work.sqlite3"
    con = sqlite3.connect(path)
    con.executescript(f"""
        CREATE TABLE t_zi_part (zi text NOT NULL, is_active text default 'Y', {', '.join(c + ' text' for c in COLS)}, desc_cn text);
        CREATE TABLE t_zi (zi text NOT NULL, pinyin text, desc_en text, is_active text default 'Y');
        CREATE TABLE t_ele_zi (zi TEXT, meaning TEXT, pinyin TEXT, is_active TEXT);
        CREATE TABLE t_part (zi text NOT NULL, meaning text, pinyin text);
        CREATE TABLE t_note (title text);
    """)
    rows = [
        _row("時", zi_left="日", zi_mid="寺"),
        _row("寺", zi_up="土", zi_down="寸"),
        _row("藻", zi_up="艹", zi_mid="澡"),
        _row("澡", zi_left="氵", zi_mid="喿"),
        _row("喿", zi_up="品", zi_down="木"),
        _row("品", zi_up="口", zi_left_down="口", zi_right_down="口"),
        _row("器", zi_left_up="口", zi_right_up="口", zi_mid="犬", zi_left_down="口", zi_right_down="口"),
        _row("哭", zi_down="犬", zi_left_up="口", zi_right_up="口"),          # stored as D, LU, RU: reading order fixes it
        _row("虹", zi_left="虫", zi_right="工"),
        _row("近", zi_left_down="辶", zi_mid="斤"),
        _row("国", zi_mid_out="囗", zi_mid="玉"),
        _row("咸", zi_mid="戌", zi_mid_in="口"),                               # uses Mi: flagged for review
        _row("半"),                                                            # a primitive: no parts
        _row("嗀", zi_left="冖 一", zi_right="殳"),                            # a position holds two parts
        _row("单", zi_right="十"),                                             # only one part
        _row("妈", zi_left="女", zi_right="?"),                                # a placeholder part
        _row("別", active="N", zi_left="另", zi_right="刂"),                   # not active
        _row("甲", zi_up="乙", zi_down="丙"),                                  # a cycle: 甲 -> 乙 -> 甲
        _row("乙", zi_up="甲", zi_down="丁"),
    ]
    con.executemany(f"INSERT INTO t_zi_part (zi, is_active, {', '.join(COLS)}) VALUES ({','.join('?' * 13)})", rows)
    con.executemany("INSERT INTO t_zi (zi, pinyin, desc_en) VALUES (?,?,?)", [
        ("時", "shi2", "time; (bound form) period/hour"), ("寺", "si4", "temple"), ("日", "ri4", "sun/day"),
        ("藻", "zao3", "algae"), ("器", "qi4", "(bound form) utensil;  device"), ("哭", "ku1", "to cry"),
        ("虹", "hong2 / jiang4", "rainbow"), ("舾", "xi1", "used in 舾裝|舾装[xi1 zhuang1]"), ("犬", "quan3", "dog"),
        ("口", "kou3", "mouth"), ("木", "mu4", "tree"), ("女", "nu:3", "female"),
    ])
    con.executemany("INSERT INTO t_ele_zi VALUES (?,?,?,?)", [("寺", "temple of words", "sì", "Y"), ("日", "sun", "rì", "Y"),
                                                              ("口", "mouth", "kǒu", "Y"), ("木", "tree", "mù", "Y")])
    con.execute("INSERT INTO t_part VALUES ('氵', 'water', 'shuǐ')")
    con.commit()
    con.close()
    return path
