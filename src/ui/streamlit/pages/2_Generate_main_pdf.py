"""Page 2: a list of characters in, main.pdf out: zitex setup, then zitex extract, then xelatex main.tex."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402

from common import WORKSPACE, need_tools, sidebar_database  # noqa: E402
from zitex.pipeline import generate_pdf, parse_chars, pdf_to_pngs  # noqa: E402
from zitex.workspace import MAX_CHARS  # noqa: E402

st.set_page_config(page_title="Generate main.pdf", page_icon="📄", layout="wide")
st.title("Generate main.pdf")
db = sidebar_database()
if db is None:
    st.stop()

st.write("The app runs the three steps of the tutorial in the workspace folder, "
         f"`{WORKSPACE}` (generated, and ignored by git):")
st.code(f"zitex setup -o workspace\nzitex extract -i {db.name} -c <your characters> -o workspace\n"
        "cd workspace && xelatex main.tex", language="bash")
if not need_tools("xelatex"):
    st.stop()

text = st.text_area("Characters", value=st.session_state.get("chars", "器,藻,佛"), key="chars_text",
                    help="Type a word or phrase such as 守株待兔 (no separator needed), or characters separated by commas or spaces. Each character is used once. At most %d are used." % MAX_CHARS, height=90)
chars = parse_chars(text)
st.caption(f"{len(chars)} character{'' if len(chars) == 1 else 's'}" + (f": {' '.join(chars[:MAX_CHARS])}" if chars else "")
           + (f". Only the first {MAX_CHARS} will be used." if len(chars) > MAX_CHARS else ""))

if st.button("Generate main.pdf", type="primary", disabled=not chars):
    with st.status("Working ...", expanded=True) as status:
        res = generate_pdf(text, db, WORKSPACE, on_step=lambda s: st.write(f"{'✔' if s.ok else '✘'} {s.name}"))
        status.update(label="Done" if res.ok else "Failed", state="complete" if res.ok else "error")
    st.session_state["result"] = res

res = st.session_state.get("result")
if res is not None:
    if res.truncated:
        st.warning(f"{res.truncated} characters were left out: at most {MAX_CHARS} are used.")
    if res.missing:
        st.warning(f"Not in the database, so left out: {' '.join(res.missing)}")
    if not res.ok:
        st.error(res.message or "Something went wrong.")
    else:
        st.success(f"{res.pdf}  ({res.pdf.stat().st_size / 1024:,.0f} KB)")
        st.download_button("Download main.pdf", res.pdf.read_bytes(), "main.pdf", "application/pdf")
        pages = pdf_to_pngs(res.pdf, WORKSPACE / "preview") if need_tools("pdftoppm") else []
        for i in range(0, len(pages), 2):
            cols = st.columns(2)
            for col, page in zip(cols, pages[i:i + 2]):
                col.image(str(page), caption=page.stem, width="stretch")
    with st.expander("What each step printed"):
        st.code(res.log or "(nothing yet)", language="text")
    main_tex = WORKSPACE / "main.tex"
    chars_yaml = WORKSPACE / "chars.yaml"
    for label, f in (("main.tex", main_tex), ("chars.yaml", chars_yaml)):
        if f.exists():
            with st.expander(label):
                st.code(f.read_text(encoding="utf-8"), language="latex" if f.suffix == ".tex" else "yaml")
