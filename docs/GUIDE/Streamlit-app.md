# The zitex Streamlit app

A small browser app with two pages:

1. **Review decompositions**: look at a character's decomposition, correct it, and work through the lists of problems.
2. **Generate main.pdf**: type a list of characters and get a PDF, using the same steps as the command line (`setup`, `extract`, `xelatex`) in the `workspace/` folder.

The pages hold no logic of their own. They call `zitex.review` and `zitex.pipeline`, which the test suite covers (including headless runs of both pages). **What the tests cannot tell you is how it looks and feels in a browser. That is what this guide is for.**

Figures below were read from `db/zitex.sqlite3` on 2026-10-02. They change as the database is edited.

## 1. Install and run

From the repository root, in the `zinets2` environment:

```bash
export PATH=/home/papagame/anaconda3/envs/zinets2/bin:$PATH     # or: conda activate zinets2
pip install -e ".[ui]"                                           # adds streamlit (1.50 or later) and pandas
streamlit run src/ui/streamlit/app.py
```

The app opens at <http://localhost:8501>. It needs `xelatex` (page 2, and the pictures on page 1) and `pdftoppm` (page images). The home page shows what it found in a caption at the bottom: `Database: ... | workspace: ... | xelatex: ... | pdftoppm: ...`.

## 2. Work on a copy of the database

**Save revision writes to the zitex file.** It never touches your working database (`zi.sqlite3`), but it does change whatever file is named in the sidebar. So validate on a copy:

```bash
# backup
cp db/zitex.sqlite3 db/zitex-orig.sqlite3
```

## 3. Page 1: Review decompositions

From the top of the page:

| Part | What it is |
|---|---|
| Metrics row | `characters`, `with warnings`, `left out`, `elemental, decomposed`, `revised` |
| **Character** box | one character (if you type more, the first is used). Starts with 佛 |
| Left column | pinyin and meaning, the shape string, the pattern, notes, warnings, a "left out of the database" error for quarantined rows, and "Used as a part in N characters" |
| Right column | a picture of the character, **Picture**: `matrix` or `tree` |
| **Revise** | an editable table with one row per part (position and one character). Delete all rows to make the character a primitive |
| Elemental checkbox | "Treat as an elemental character (it is then never expanded inside other characters)" |
| **Why (kept with the revision)** | a note stored with the revision |
| Buttons | **Check the change** (try it, write nothing), **Save revision**, **Revert to the original** (enabled once a revision exists) |
| **What to review** | the **List** selector and a table. Select a row, then **Open X** to load that character above |
| **Revisions** | the revisions made so far, and **Download the revisions (CSV)** |

The **List** choices, with the counts you should see at the start:

| List | Count |
|---|---|
| Left out of the database (cannot be converted yet) | 223 |
| Elemental characters that still have a decomposition | 160 |
| Patterns that use Mi (to review) | 218 |
| A radical is labelled M (W8) | 88 |
| Position regions overlap (W7) | 14 |
| Revised by hand | 1 |

The "Mi" list says 218, and the plan's other documents say 113. Both are right: 113 characters have `Mi` in their **first-level** pattern, and 218 counts nested levels as well.

## 4. Validation checklist (page 1)

Start with the copy in the sidebar. Tick each box as you go.

**The starting numbers**

- [ ] The metrics read: characters 5,982, with warnings 102, left out 223, elemental decomposed 160, revised 1.

**Looking at characters** (type each in **Character**)

- [ ] **佛**: pattern `L-M`, parts 亻 and 弗, and 弗 is a leaf (it is elemental). The revision note is not shown here (the revision is on 弗).
- [ ] **弗**: "A primitive: no decomposition", and the green "Revised on ..." message.
- [ ] **三**: still shown with its three parts (一, 一, 一). It is on the elemental-decomposed list.
- [ ] **攸**, **咸**: they show their decomposition and any warning or review note.
- [ ] **時**: the pinyin shows `?`. That means the database has no pinyin for it, not that the app failed.
- [ ] **冠**: shows a warning.
- [ ] The **Picture** switch changes between the matrix and the tree for one character.
- [ ] A character that is not in the database (try 龘): "is not in this database. You can add it below by giving its parts."

**Revise 三 to a primitive, then revert** (reversible)

- [ ] Delete all rows of the **Revise** table, tick the elemental checkbox, press **Check the change**. You see `After the change: ...` with pattern `none` and "No warnings." Nothing is saved yet.
- [ ] Press **Save revision**. The metrics become: elemental, decomposed **159**, revised **2**. Searching 叁 now gives `⿳厶大三`, and 王 gives `<M-Mi>三丨`.
- [ ] Press **Revert to the original**. The metrics return to 160 and 1.

**Revise 冠 to U / LD / RD, then revert**

- [ ] In the table set the three parts to positions `U`, `LD`, `RD` and press **Check the change**. Then **Save revision**: with warnings **101**, revised **2**.
- [ ] **Revert to the original**: back to 102 and 1.

**Other things to try**

- [ ] Enter two parts at the same position, or a part with two characters: the error message is clear, and nothing is written.
- [ ] Choose each **List**, select a row, press **Open X**: the character loads at the top.
- [ ] **Download the revisions (CSV)** gives a file with the revision(s).
- [ ] After a revision, stop the app and start it again: the revision is still there.

## 5. Page 2: Generate main.pdf

1. Type characters in **Characters**: a word or phrase with no separator (`守株待兔` becomes 守 株 待 兔), or characters separated by commas, spaces or new lines (`器,藻,佛` is filled in). Punctuation is skipped, repeats are dropped, and at most 60 are used. The caption lists the characters it found.
2. Press **Generate main.pdf**. A status box shows the three steps as they run.
3. The result: page images, **Download main.pdf**, and an expander **What each step printed** with the logs, `main.tex` and `chars.yaml`.

It does exactly this, in `workspace/` (generated, and git-ignored):

```bash
zitex setup -o workspace
zitex extract -i <database> -c 器,藻,佛 -o workspace
cd workspace && xelatex main.tex
```

## 6. Validation checklist (page 2)

- [ ] **器,藻,佛** makes a PDF with **2 pages**. `workspace/` then holds `chars.yaml`, `lexicon.yaml`, `main.tex`, `zitex.sty`, `fonts.yaml`, `fallback.yaml`, `glyphs/`, `zitex-out/` and `main.pdf`.
- [ ] The PDF matches what `xelatex main.tex` makes by hand in that folder.
- [ ] Mixing in an unknown character (**器,龘,佛**): the PDF is still made, and a warning says `Not in the database, so left out: 龘`.
- [ ] **龘** alone: no PDF, and the message says `extract failed: not in ...: 龘`.
- [ ] More than 60 characters: only the first 60 are used, with a warning saying how many were left out.
- [ ] After a revision on page 1 (say 弗), generating **佛** reflects it. Use the same database in the sidebar.
- [ ] Generate twice in a row: the second run replaces the first without complaint.
- [ ] The **Generate main.pdf** button is disabled when the box is empty.

## 7. How it works

- A revision is stored in the `zx_revision` table of the zitex file, and applied to `zx_part` and `zx_char`. The first revision of a character remembers the original, which **Revert to the original** returns to.
- **Revisions survive `zitex db-build`.** A rebuild applies them again (it prints `re-applied N revision(s)`).
- The working database (`zi.sqlite3`) is never written by the app or by zitex. To bring a revision there, use the CSV list of revisions.
- The picture on page 1 and the preview in **Check the change** are made from a **throw-away copy** of the database, so checking never changes your file.
- Page 2 calls the command line in a subprocess (`python -m zitex ...`), so what you get is what the commands give.

## 8. If something goes wrong

| Symptom | Cause and fix |
|---|---|
| `streamlit: command not found` | activate `zinets2`, and run `pip install -e ".[ui]"` |
| the sidebar says the database is not found, or has no zx_ tables | give the path to a file made by `zitex db-build` (such as `db/zitex.sqlite3`), not the raw `zi.sqlite3` |
| no picture on page 1 | `xelatex` or `pdftoppm` is missing (see the caption on the home page) |
| page 2 fails at `xelatex` | open **What each step printed**: the last lines of the log say which package or font is missing |
| pinyin shows `?` | the database has no pinyin for that character (351 characters in the first iteration) |
| a revision is rejected | the message says why: a position is not one of `L R M U D Mi Mo LU LD RU RD`, a part is not exactly one character, or there is one part (a character has two or more, or none) |
| the page does not update after an edit outside the app | reload the browser tab |

## 9. Known limits

- Tested headlessly only (Streamlit's `AppTest`, plus the server starting and answering its health check). Layout, widths and the feel of the table editor in a real browser are **not verified**. Please note anything awkward.
- One person, one file: there is no locking, so do not run two copies of the app on the same database file.
