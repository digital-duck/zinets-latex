"""Page 1: look at how a character is decomposed, try a change, and save it as a revision."""
import csv
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from common import need_tools, sidebar_database  # noqa: E402
from zitex import zxdb  # noqa: E402
from zitex.ops import POSITIONS  # noqa: E402
from zitex.pipeline import preview_png  # noqa: E402
from zitex.review import KINDS, issue_rows, level_of, load_review, preview_revision  # noqa: E402

st.set_page_config(page_title="Review decompositions", page_icon="🔎", layout="wide")
st.title("Review decompositions")
db = sidebar_database()
if db is None:
    st.stop()


@st.cache_data(show_spinner="Reading the database ...")
def cached_review(path: str, stamp: float):
    return load_review(path)


data = cached_review(str(db), db.stat().st_mtime)

cols = st.columns(len(data.counts))
for col, (name, n) in zip(cols, data.counts.items()):
    col.metric(name, f"{n:,}")

# ---- the character -------------------------------------------------------------------------------------------------
st.session_state.setdefault("char", "佛")
st.text_input("Character", key="char", help="One character (if you type more, the first is used). It must be in the database.")
zi = st.session_state["char"].strip()[:1]
if not zi:
    st.stop()
entry = data.entries.get(zi)
quarantined = next((q for q in data.quarantine if q[0] == zi), None)
revision = next((r for r in data.revisions if r["zi"] == zi), None)

left, right = st.columns([3, 2])
with left:
    st.markdown(f"## {zi}")
    if entry is None and quarantined is None:
        st.warning(f"{zi} is not in this database. You can add it below by giving its parts.")
    if entry is not None:
        st.write(f"**{entry.pinyin or '?'}** · {entry.meaning or 'no meaning'}")
        st.code(entry.shape, language=None)
        if entry.tree.pattern:
            st.write(f"Pattern **{entry.tree.pattern}**")
        else:
            st.write("A primitive: no decomposition.")
        for note in (entry.note, entry.review):
            if note:
                st.info(note)
        for w in data.warnings.get(zi, []):
            st.warning(str(w))
    if quarantined:
        st.error(f"Left out of the database: {quarantined[1]}.  Cells: `{quarantined[2]}`")
    if revision:
        st.success(f"Revised on {revision['ts']}. {revision.get('note') or ''}")
    users = data.used_in.get(zi, [])
    if users:
        st.caption(f"Used as a part in {len(users)} characters: {' '.join(users[:40])}{' ...' if len(users) > 40 else ''}"
                   .replace(" ...", " and more"))
with right:
    if entry is not None and need_tools("xelatex", "pdftoppm"):
        style = st.radio("Picture", ["matrix", "tree"], horizontal=True, key="style")
        png = preview_png(entry, style)
        if png:
            st.image(png)

# ---- revise --------------------------------------------------------------------------------------------------------
st.subheader("Revise")
st.caption("One row per part of this character, with its position. Delete all the rows to make it a primitive. "
           "Positions: " + " ".join(POSITIONS) + ".")
stored = level_of(db, zi)
key = f"editor-{zi}-{len(data.revisions)}-{db.stat().st_mtime}"
frame = pd.DataFrame(stored or [("", "")], columns=["pos", "part"])
edited = st.data_editor(
    frame, key=key, num_rows="dynamic", width="stretch",
    column_config={"pos": st.column_config.SelectboxColumn("position", options=list(POSITIONS), required=False),
                   "part": st.column_config.TextColumn("part (one character)")})
rows = [(str(p or ""), str(c or "")) for p, c in edited.itertuples(index=False)]
was_elemental = zi in data.elemental
elemental = st.checkbox("Treat as an elemental character (it is then never expanded inside other characters)",
                        value=was_elemental, key=f"el-{key}")
elemental_flag = True if elemental else (False if was_elemental else None)       # None: leave the flag alone
note = st.text_input("Why (kept with the revision)", key=f"note-{key}")

c1, c2, c3 = st.columns(3)
check = c1.button("Check the change")
save = c2.button("Save revision", type="primary")
revert = c3.button("Revert to the original", disabled=revision is None)

if check or save:
    prev = preview_revision(db, zi, rows, elemental=elemental_flag)
    if prev.error:
        st.error(prev.error)
    else:
        st.write(f"After the change: `{prev.shape}`  ·  pattern **{prev.pattern or 'none'}**")
        for w in prev.warnings:
            st.warning(str(w))
        if not prev.warnings:
            st.success("No warnings.")
        if save:
            zxdb.revise(db, zi, rows, note=note or None, elemental=elemental_flag)
            st.cache_data.clear()
            st.toast(f"Saved the revision of {zi}")
            st.rerun()
if revert:
    zxdb.revert(db, zi)
    st.cache_data.clear()
    st.toast(f"Reverted {zi}")
    st.rerun()

# ---- what to review ------------------------------------------------------------------------------------------------
st.divider()
st.subheader("What to review")
kind = st.selectbox("List", list(KINDS), format_func=lambda k: f"{KINDS[k]}  ({len(issue_rows(data, k)):,})")
table = issue_rows(data, kind)
if table:
    st.caption("Select a row to open that character above.")
    frame = pd.DataFrame(table)
    sel = st.dataframe(frame, width="stretch", hide_index=True, on_select="rerun", selection_mode="single-row",
                       height=320, key=f"table-{kind}")
    picked = sel.selection.rows if sel and sel.selection else []
    if picked:
        chosen = frame.iloc[picked[0]]["char"]
        if chosen != zi:
            # a callback, not an assignment after the button: the "char" box already exists in this run, and Streamlit
            # only lets session state of a widget change before it is drawn (callbacks run first)
            st.button(f"Open {chosen}", on_click=lambda c=chosen: st.session_state.update(char=c))
else:
    st.info("Nothing in this list.")

# ---- the revisions -------------------------------------------------------------------------------------------------
st.divider()
st.subheader("Revisions")
if data.revisions:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["zi", "revised_parts", "original_parts", "elemental", "note", "when"])
    for r in data.revisions:
        w.writerow([r["zi"], " ".join(f"{p}={c}" for p, c in r["parts"]),
                    " ".join(f"{p}={c}" for p, c in (r["original"] or {}).get("parts", [])),
                    "" if r.get("elemental") is None else r["elemental"], r.get("note") or "", r.get("ts") or ""])
    st.dataframe(pd.DataFrame(issue_rows(data, "revised")), width="stretch", hide_index=True)
    st.download_button("Download the revisions (CSV)", buf.getvalue().encode("utf-8"), "zitex-revisions.csv", "text/csv")
    st.caption("Revisions live in the zitex file. To apply them to your working database, use this list: "
               "that file is never changed by zitex.")
else:
    st.caption("No revisions yet.")
