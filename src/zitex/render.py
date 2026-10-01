"""Renderers: turn a decomposition tree into TikZ/LaTeX source (XeLaTeX).

Every ``render_*`` function returns a self-contained snippet, with no document
wrapper and no dependency on ``zitex.sty``. The host document needs ``tikz``,
``fontspec`` and ``xeCJK``, a CJK main font, and ∴ ∵ (U+2234, U+2235) in the CJK character class. ``document()`` builds such a host.

Styles:
  tree     decomposition tree, growing to the right, with a position label per edge
  formula  one line: ``A + B + C -> X``
  matrix   nested boxes laid out by operator (the Zi-Matrix view)
"""
from __future__ import annotations

import contextvars

from .fonts import CURRENT, FontConfig, Resolver
from .loader import Entry, role_kinds
from .ops import FLAT_OPS, is_general
from .tree import Node

PT_PER_CM = 28.4528

# role -> (fill rgb, text rgb); roles come from an entry's `role` mapping
ROLE_FILL = {
    "semantic": (214, 234, 248),
    "phonetic": (252, 228, 214),
    "force": (226, 240, 217),
    "both": (232, 222, 245),      # a component that is both semantic and phonetic
}

# which reading of an entry's roles is being rendered (None: the entry's default)
READING: contextvars.ContextVar[str | None] = contextvars.ContextVar("zitex_reading", default=None)
DEFAULT_FILL = (248, 249, 250)
BORDER = (44, 62, 80)
ACCENT = (231, 76, 60)
MUTED = (127, 140, 141)

_ESCAPES = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
    "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


def esc(text: str) -> str:
    """Escape LaTeX special characters in free text (pinyin, meaning, ...)."""
    return "".join(_ESCAPES.get(ch, ch) for ch in text)


_COLORS = {
    "zi-border": BORDER, "zi-accent": ACCENT, "zi-muted": MUTED, "zi-default": DEFAULT_FILL,
    "zi-semantic": ROLE_FILL["semantic"], "zi-phonetic": ROLE_FILL["phonetic"], "zi-force": ROLE_FILL["force"],
    "zi-both": ROLE_FILL["both"],
}


def _defs() -> str:
    """One \\definecolor line per colour; each snippet carries its own so it stays self-contained."""
    return "\n".join("\\definecolor{%s}{RGB}{%d,%d,%d}" % ((k,) + v) for k, v in _COLORS.items())


def _g(ch: str) -> str:
    """A component as typeset text: the character itself, or font/image markup when it needs a fallback."""
    res = CURRENT.get()
    return res.glyph(ch) if res else ch


def _tg(ch: str) -> str:
    """Same, inside math."""
    return r"\text{" + _g(ch) + "}"


def _rgb(c: tuple[int, int, int]) -> str:
    for name, v in _COLORS.items():
        if v == c:
            return name
    raise KeyError(c)


def _fill(c: str | None, role: dict) -> tuple[int, int, int]:
    kinds = role_kinds(role.get(c or ""))
    if "semantic" in kinds and "phonetic" in kinds:
        return ROLE_FILL["both"]
    return ROLE_FILL.get(kinds[0] if kinds else "", DEFAULT_FILL)


def _roles(e: Entry) -> dict:
    """Roles of the entry under the reading being rendered."""
    return e.roles_for(READING.get())


def _flat(n: Node) -> str:
    """Component characters of a subtree, left to right (used where only a label fits)."""
    if n.is_leaf or n.c:
        return _g(n.c or "")
    return "".join(_flat(p) for p in n.parts)


# ---- formula ----------------------------------------------------------------

def _term(n: Node, show_pos: bool) -> str:
    if n.is_leaf or n.c:
        t = _g(n.c or "")
    else:  # anonymous composite: show its parts in brackets
        t = "(" + " + ".join(_term(p, show_pos) for p in n.parts) + ")"
    if show_pos and n.pos:
        t += r"\textsubscript{\scriptsize " + n.pos + "}"
    return t


def render_formula(e: Entry, show_pos: bool = False, info: bool = True, lex=None, lang: str = "en") -> str:
    """``日 + 寺 → 時 (shí, time)``. Anonymous composites are shown in brackets.

    With a lexicon, pinyin and meaning come from it (meaning in ``lang``); otherwise from the entry.
    """
    terms = " + ".join(_term(p, show_pos) for p in e.tree.parts) if not e.tree.is_leaf else e.char
    out = f"{terms} $\\rightarrow$ \\textbf{{{_g(e.char)}}}"
    if info:
        py = (lex.get_pinyin(e.char) if lex else None) or e.pinyin
        mean = (lex.get_gloss(e.char, lang) if lex else None) or e.meaning
        if py or mean:
            out += " {\\small(" + ", ".join(esc(x) for x in (py, mean) if x) + ")}"
    return out


# ---- math (MathJax / KaTeX / amsmath) ---------------------------------------
# The same equation grammar conceptbook-app already shows:
#   \underbrace{\overset{\text{nǚ}}{\text{女}}}_{\text{woman}} + ... = \underbrace{\overset{\text{hǎo}}{\text{好}}}_{\text{good}}
# Only \text, \overset, \underbrace, \xrightarrow, \left/\right and \times are used, so it works
# unchanged in MathJax 3 and in XeLaTeX with amsmath.

ARROW_WORDS = {  # reaction-arrow labels for component roles
    "en": {"phonetic": "sound", "semantic": "meaning", "force": "force"},
    "fr": {"phonetic": "son", "semantic": "sens", "force": "force"},
}


def _t(text: str) -> str:
    return r"\text{" + esc(text) + "}"


def _mterm(n: Node, lex, lang: str, show_pos: bool, pinyin: bool, gloss: bool) -> str:
    if not n.is_leaf and not n.c:  # anonymous composite: its parts in brackets
        inner = " + ".join(_mterm(p, lex, lang, show_pos, pinyin, gloss) for p in n.parts)
        return r"\left(" + inner + r"\right)"
    ch = n.c or ""
    glyph = _tg(ch) + (r"_{" + _t(n.pos) + "}" if show_pos and n.pos else "")
    py = lex.get_pinyin(ch) if (lex and pinyin) else None
    if py:
        glyph = r"\overset{" + _t(py) + "}{" + glyph + "}"
    g = lex.get_gloss(ch, lang) if (lex and gloss) else None
    if g:
        glyph = r"\underbrace{" + glyph + "}_{" + _t(g) + "}"
    return glyph


def _collapse(parts: list[Node]) -> list[tuple[int, Node]]:
    """Merge neighbouring identical leaves: 口 + 口 + 口 -> (3, 口)."""
    out: list[tuple[int, Node]] = []
    for p in parts:
        if out and p.is_leaf and out[-1][1].is_leaf and out[-1][1].c == p.c:
            out[-1] = (out[-1][0] + 1, out[-1][1])
        else:
            out.append((1, p))
    return out


def render_math(e: Entry, lex=None, lang: str = "en", arrow: str = "=", collapse: bool = False,
                show_pos: bool = False, pinyin: bool = True, gloss: bool = True,
                wrap: str = "display", result: str = "below") -> str:
    """Decomposition as a typeset equation, with pinyin above and gloss below each piece.

    arrow:    "="        plain equals sign (conceptbook-app style)
              "reaction" a right arrow
              "role"     an arrow labelled with the roles stored on the entry (sound / meaning)
    collapse: 3 x 口 instead of 口 + 口 + 口
    wrap:     "display" -> \\[ ... \\],  "inline" -> \\( ... \\),  "none" -> bare math
    result:   "below" -> gloss under the result, like the pieces;  "paren" -> (\\textit{gloss}) after it
    """
    if e.tree.is_leaf:
        parts: list[tuple[int, Node]] = [(1, e.tree)]
    elif collapse:
        parts = _collapse(e.tree.parts)
    else:
        parts = [(1, p) for p in e.tree.parts]
    terms = []
    for k, p in parts:
        t = _mterm(p, lex, lang, show_pos, pinyin, gloss)
        terms.append((f"{k}\\times " if k > 1 else "") + t)
    lhs = " + ".join(terms)

    roles = _roles(e)
    if arrow == "role" and roles:
        words = ARROW_WORDS.get(lang, ARROW_WORDS["en"])
        label = ", ".join(f"{words.get(r, r)}: {(lex.get_pinyin(c) if lex else None) or c}"
                          for c, r in roles.items() if "phonetic" in role_kinds(r))
        sym = r"\xrightarrow{" + _t(label) + "}" if label else "="
    elif arrow == "reaction":
        sym = r"\longrightarrow"
    else:
        sym = "="

    res = _tg(e.char)
    py = lex.get_pinyin(e.char) if lex and pinyin else e.pinyin
    if py:
        res = r"\overset{" + _t(py) + "}{" + res + "}"
    g = (lex.get_gloss(e.char, lang) if lex else e.meaning) if gloss else None
    if g and result == "paren":
        rhs = res + r"\ (\textit{" + esc(g) + "})"
    elif g:
        rhs = r"\underbrace{" + res + "}_{" + _t(g) + "}"  # same style as the pieces on the left
    else:
        rhs = res
    body = f"{lhs} {sym} {rhs}"
    return {"display": "\\[ " + body + " \\]", "inline": "\\( " + body + " \\)"}.get(wrap, body)


# ---- tree -------------------------------------------------------------------

def render_tree(e: Entry, dx: float = 2.4, dy: float = 0.85) -> str:
    """Horizontal tree: root on the left, leaves on the right, position label on each edge."""
    nodes: list[tuple[str, Node, float, float, str | None]] = []  # name, node, x, y, parent
    leaf_row = [0]

    def assign(n: Node, depth: int, parent: str | None) -> float:
        idx = len(nodes)
        name = f"n{idx}"
        nodes.append((name, n, depth * dx, 0.0, parent))  # y filled in below
        if n.is_leaf:
            y = -leaf_row[0] * dy
            leaf_row[0] += 1
        else:
            ys = [assign(p, depth + 1, name) for p in n.parts]
            y = sum(ys) / len(ys)
        nodes[idx] = (name, n, depth * dx, y, parent)
        return y

    assign(e.tree, 0, None)
    pos_of = {name: (x, y) for name, _, x, y, _ in nodes}
    border = _rgb(BORDER)

    out = [
        _defs(),
        r"\begin{tikzpicture}[",
        rf"  zinode/.style={{draw={border}, rounded corners=1.5pt, inner sep=3pt, minimum height=0.65cm, minimum width=0.65cm, font=\large}},",
        rf"  zipos/.style={{font=\tiny, text={_rgb(MUTED)}, fill=white, inner sep=1pt}}",
        r"]",
    ]
    for name, n, x, y, parent in nodes:
        if parent is None:
            style = rf"zinode, line width=0.9pt, draw={_rgb(ACCENT)}, fill={_rgb(DEFAULT_FILL)}, font=\LARGE\bfseries"
            label = _g(e.char)
        else:
            style = f"zinode, fill={_rgb(_fill(n.c, _roles(e)))}"
            if n.is_leaf:
                label = _g(n.c or "")
            elif n.c:
                label = _g(n.c) + r"\,{\small " + _op_text(n.op or "") + "}"
            else:
                label = r"{\large " + _op_text(n.op or "") + "}"
        out.append(rf"  \node[{style}] ({name}) at ({x:.2f},{y:.2f}) {{{label}}};")
    for name, n, x, y, parent in nodes:
        if parent is None:
            continue
        out.append(rf"  \draw[draw={border}!60] ({parent}.east) -- ++({(dx - 0.9) / 2:.2f},0) |- ({name}.west);")
        if n.pos:
            out.append(rf"  \node[zipos, anchor=east] at ([xshift=-0.06cm]{name}.west) {{{n.pos}}};")
    out.append(r"\end{tikzpicture}")
    return "\n".join(out)


# ---- matrix -----------------------------------------------------------------

def flat_rects(labels: list[str]) -> list[tuple[float, float, float, float]]:
    """Unit-square rectangles (x, y, w, h; origin bottom-left) for the labels of a flat pattern.

    Patterns with L or R are laid out in columns, all others in rows (top, middle, bottom).
    Inside a row or column the parts follow reading order. A lone U or D part is centered at half
    width when the opposite row has two parts, which gives the triangle look of ∴ and ∵.
    """
    rects: list[tuple[float, float, float, float] | None] = [None] * len(labels)
    idx = range(len(labels))
    if any(l in ("L", "R") for l in labels):
        groups = [[i for i in idx if labels[i] in g] for g in (("L", "LU", "LD"), ("M",), ("R", "RU", "RD"))]
        groups = [g for g in groups if g]
        for ci, g in enumerate(groups):
            order = sorted(g, key=lambda i: 0 if labels[i] in ("LU", "RU") else 2 if labels[i] in ("LD", "RD") else 1)
            for k, i in enumerate(order):
                rects[i] = (ci / len(groups), 1 - (k + 1) / len(order), 1 / len(groups), 1 / len(order))
    else:
        groups = [[i for i in idx if labels[i] in g] for g in (("U", "LU", "RU"), ("M",), ("D", "LD", "RD"))]
        groups = [g for g in groups if g]
        widest = max((len(g) for g in groups), default=1)
        for ri, g in enumerate(groups):
            order = sorted(g, key=lambda i: 0 if labels[i] in ("LU", "LD") else 1 if labels[i] in ("U", "D", "M") else 2)
            for k, i in enumerate(order):
                w = 1 / len(order)
                x0 = k * w
                if len(order) == 1 and labels[i] in ("U", "D") and widest > 1:
                    w, x0 = 0.5, 0.25
                rects[i] = (x0, 1 - (ri + 1) / len(groups), w, 1 / len(groups))
    return [r if r else (0.0, 0.0, 1.0, 1.0) for r in rects]


def _op_text(op: str) -> str:
    """Operator as shown in a tree: the symbol, or the pattern when the symbol has no glyph."""
    if op == "⁙":
        return r"{\scriptsize LU-RU-M-LD-RD}"
    if is_general(op):
        return r"{\scriptsize " + op[1:-1] + "}"
    return op


def _size_pt(w: float, h: float, k: float = 0.62) -> str:
    pt = max(4.0, k * min(w, h) * PT_PER_CM)
    return rf"\fontsize{{{pt:.1f}pt}}{{{pt:.1f}pt}}\selectfont"


def render_matrix(e: Entry, size: float = 4.4) -> str:
    """Zi-Matrix: nested boxes laid out by operator. Enclosures nest, they are not grid cells."""
    out = [_defs(), r"\begin{tikzpicture}[every node/.style={inner sep=0pt, outer sep=0pt, align=center}]"]
    border = _rgb(BORDER)

    def rect(x, y, w, h, fill=None, style=""):
        f = f"fill={_rgb(fill)}, " if fill else ""
        out.append(rf"  \draw[draw={border}!70, {f}{style}] ({x:.3f},{y:.3f}) rectangle ({x + w:.3f},{y + h:.3f});")

    def glyph(text, cx, cy, w, h, k=0.62, extra=""):
        out.append(rf"  \node[{extra}] at ({cx:.3f},{cy:.3f}) {{{_size_pt(w, h, k)} {text}}};")

    def tag(n: Node, x, y, w, h):
        """Name of a composite, as a small label in its top-left corner."""
        if n.c and not n.is_leaf:
            out.append(rf"  \node[anchor=north west, text={_rgb(MUTED)}] at ({x + 0.03:.3f},{y + h - 0.02:.3f}) {{\fontsize{{5pt}}{{5pt}}\selectfont {_g(n.c)}}};")

    def box(n: Node, x, y, w, h, opacity: float | None = None):
        g = 0.03  # gap between neighbours
        x, y, w, h = x + g, y + g, w - 2 * g, h - 2 * g
        if opacity is not None:
            out.append(rf"  \begin{{scope}}[opacity={opacity}, text opacity={opacity}]")
        if n.is_leaf:
            rect(x, y, w, h, _fill(n.c, e.role))
            glyph(_g(n.c or ""), x + w / 2, y + h / 2, w, h)
        else:
            rect(x, y, w, h, None, "thin")
            tag(n, x, y, w, h)
            layout(n, x, y, w, h)
        if opacity is not None:
            out.append(r"  \end{scope}")

    def rows(n, x, y, w, h):          # top to bottom
        k = len(n.parts)
        for i, p in enumerate(n.parts):
            box(p, x, y + h - (i + 1) * h / k, w, h / k)

    def cols(n, x, y, w, h):          # left to right
        k = len(n.parts)
        for i, p in enumerate(n.parts):
            box(p, x + i * w / k, y, w / k, h)

    def surround(n, x, y, w, h):
        outer, inner = n.parts
        t = 0.28 * min(w, h)
        op = n.op
        # inner region and where the outer component's label goes
        if op == "⿴":   ir, lab = (x + t, y + t, w - 2 * t, h - 2 * t), (x + t / 2, y + h - t / 2)
        elif op == "⿵": ir, lab = (x + t, y, w - 2 * t, h - t), (x + w / 2, y + h - t / 2)
        elif op == "⿶": ir, lab = (x + t, y + t, w - 2 * t, h - t), (x + w / 2, y + t / 2)
        elif op == "⿷": ir, lab = (x + t, y + t, w - t, h - 2 * t), (x + t / 2, y + h / 2)
        elif op == "⿸": ir, lab = (x + t, y, w - t, h - t), (x + t / 2, y + h - t / 2)
        elif op == "⿹": ir, lab = (x, y, w - t, h - t), (x + w - t / 2, y + h - t / 2)
        else:           ir, lab = (x + t, y + t, w - t, h - t), (x + t / 2, y + t / 2)  # ⿺
        rect(x, y, w, h, _fill(outer.c, _roles(e)), "thin")
        glyph(_flat(outer), lab[0], lab[1], t, t, 0.8)
        box(inner, *ir)

    def overlay(n, x, y, w, h):
        a, b = n.parts
        box(a, x, y, w, h)
        box(b, x, y, w, h, opacity=0.55)

    def flat(n, x, y, w, h):
        """Any flat pattern (∴ ∵ ∷ ⁙ and <pattern>): place each child by its position label."""
        for p, (rx, ry, rw, rh) in zip(n.parts, flat_rects([q.pos or "M" for q in n.parts])):
            box(p, x + rx * w, y + ry * h, rw * w, rh * h)

    def layout(n, x, y, w, h):
        if n.op in ("⿱", "⿳"):
            rows(n, x, y, w, h)
        elif n.op in ("⿰", "⿲"):
            cols(n, x, y, w, h)
        elif n.op in ("⿴", "⿵", "⿶", "⿷", "⿸", "⿹", "⿺"):
            surround(n, x, y, w, h)
        elif n.op == "⿻":
            overlay(n, x, y, w, h)
        elif n.op in FLAT_OPS or is_general(n.op or ""):
            flat(n, x, y, w, h)
        else:
            rows(n, x, y, w, h)

    root = e.tree
    if root.is_leaf:
        rect(0, 0, size, size, _fill(root.c, _roles(e)))
        glyph(_g(root.c or ""), size / 2, size / 2, size, size)
    else:
        rect(0, 0, size, size, DEFAULT_FILL, "thick")
        layout(root, 0, 0, size, size)
    out.append(r"\end{tikzpicture}")
    return "\n".join(out)


# ---- dispatch and document wrapper ------------------------------------------

STYLES = {"tree": render_tree, "formula": render_formula, "matrix": render_matrix, "math": render_math}


def render_with(e: Entry, style: str = "tree", fonts: FontConfig | None = None, reading: str | None = None,
                **kw) -> tuple[str, Resolver | None]:
    """Render, resolving glyphs through `fonts`. Returns the snippet and the resolver
    (which lists missing components and SVG files that were used).

    `reading` picks which named reading of the roles colours the pieces and labels the arrow
    (an entry without it uses its default reading)."""
    if style not in STYLES:
        raise ValueError(f"unknown style {style!r}; choose from {sorted(STYLES)}")
    resolver = Resolver(fonts) if fonts else None
    token, rtoken = CURRENT.set(resolver), READING.set(reading)
    try:
        out = STYLES[style](e, **kw)
    finally:
        CURRENT.reset(token)
        READING.reset(rtoken)
    if resolver and resolver.used:
        out = resolver.prelude + "\n" + out
    return out, resolver


def render(e: Entry, style: str = "tree", fonts: FontConfig | None = None, reading: str | None = None, **kw) -> str:
    return render_with(e, style, fonts, reading, **kw)[0]


def document(body: str, font: str = "Noto Serif CJK SC", standalone: bool = True, zitexpath: str | None = None) -> str:
    """Wrap snippets in a minimal XeLaTeX document (for PDF output)."""
    cls = r"\documentclass[border=6pt,varwidth]{standalone}" if standalone else r"\documentclass{article}"
    return "\n".join([
        cls,
        r"\usepackage{fontspec}",
        r"\usepackage{xeCJK}",
        rf"\setCJKmainfont{{{font}}}",
        r'\xeCJKDeclareCharClass{CJK}{"2234,"2235,"2237}  % the ZiNets operators ∴ ∵ ∷',
        r"\usepackage{amsmath}",
        r"\usepackage{graphicx}",
        r"\usepackage{tikz}",
        *([rf"\def\zitexpath{{{zitexpath}}}"] if zitexpath else []),
        r"\begin{document}",
        body,
        r"\end{document}",
        "",
    ])
