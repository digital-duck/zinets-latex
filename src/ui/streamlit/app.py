"""zitex: review the decompositions, and typeset a list of characters.

Run from anywhere:   streamlit run src/ui/streamlit/app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st  # noqa: E402

from common import ROOT, WORKSPACE, sidebar_database, tools_status  # noqa: E402

st.set_page_config(page_title="zitex", page_icon="字", layout="wide")
db = sidebar_database()

st.title("zitex")
st.write("Chinese character decompositions, typeset through XeLaTeX. Two pages, in the sidebar:")
c1, c2 = st.columns(2)
with c1:
    st.subheader("1. Review decompositions")
    st.write("Look up a character, see how it is decomposed, and correct it. Corrections are saved in the zitex "
             "database as *revisions*, and survive `zitex db-build`.")
    st.page_link("pages/1_Review_decompositions.py", label="Open the review page", icon="🔎")
with c2:
    st.subheader("2. Generate main.pdf")
    st.write("Give a list of characters. The app runs `zitex setup`, `zitex extract` and `xelatex main.tex` in the "
             "workspace folder, and shows the PDF.")
    st.page_link("pages/2_Generate_main_pdf.py", label="Open the generate page", icon="📄")

st.divider()
have = tools_status()
st.caption(f"Database: {db if db else 'not set'}  |  workspace: {WORKSPACE}  |  xelatex: "
           f"{'found' if have['xelatex'] else 'missing'}  |  pdftoppm: {'found' if have['pdftoppm'] else 'missing'}")
