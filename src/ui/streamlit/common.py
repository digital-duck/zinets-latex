"""Shared pieces of the zitex Streamlit app: where things are, and the database chosen in the sidebar."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[3]            # the zitex checkout: src/ui/streamlit/common.py -> three levels up
WORKSPACE = ROOT / "workspace"                         # generated: git-ignored, safe to delete

from zitex import zxdb                                  # noqa: E402
from zitex.sources import find_default_database, is_sqlite  # noqa: E402


def sidebar_database() -> Path | None:
    """The database text box of the sidebar, shared by both pages through st.session_state."""
    if "db" not in st.session_state:
        found = find_default_database(ROOT)
        st.session_state["db"] = str(found) if found else str(ROOT / "db" / "zitex.sqlite3")
    with st.sidebar:
        st.header("Database")
        st.text_input("zitex database (zx_ tables)", key="db", help="Made by `zitex db-build`. Revisions are saved here, "
                      "never in your working database.")
        path = Path(st.session_state["db"]).expanduser()
        if not path.is_file():
            st.error(f"No such file: {path}")
            return None
        if not is_sqlite(path):
            st.error("Not a SQLite database.")
            return None
        if not zxdb.has_zx(path):
            if zxdb.has_raw(path):
                st.warning("This is the raw working database. Run `zitex db-build` to make a zitex file, and point "
                           "this box at it: revisions need one.")
            else:
                st.error("This file has neither the zx_ tables nor the working tables.")
            return None
        st.caption(f"{path.stat().st_size / 1024:,.0f} KB")
        return path


def tools_status() -> dict[str, bool]:
    return {"xelatex": shutil.which("xelatex") is not None, "pdftoppm": shutil.which("pdftoppm") is not None}


def need_tools(*names: str) -> bool:
    """Show a message for each missing tool, and say whether all of them are there."""
    have = tools_status()
    missing = [n for n in names if not have.get(n, shutil.which(n) is not None)]
    for n in missing:
        st.warning(f"`{n}` is not installed, so this part is unavailable.")
    return not missing


def python_info() -> str:
    return f"{sys.version.split()[0]}"
