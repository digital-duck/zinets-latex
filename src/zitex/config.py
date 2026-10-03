"""Sizes, spacings and colours of the zitex views, in one place.

Change a value here and every snippet written afterwards follows it. Lengths are in cm unless the name says
otherwise. A few settings are TeX font commands (``\\small``) because that is what the snippets use.

Re-run ``zitex extract`` or ``zitex render`` after a change: the snippets in ``zitex-out/`` are written by Python,
so existing ones keep the old sizes.
"""

# ---- matrix  (\zimatrix) ---------------------------------------------------------------------------------------
MATRIX_SIZE_CM = 2.2          # side of the whole square. It was 4.4 until 2026-10-03 (now half)
MATRIX_GAP_RATIO = 0.03 / 4.4  # gap between neighbouring boxes, as a fraction of the side (so it scales with the size)
MATRIX_GLYPH_RATIO = 0.62     # a character fills this fraction of the smaller side of its box
MATRIX_SURROUND_GLYPH_RATIO = 0.8  # the same, for the outer component of an enclosing pattern (⿵ ⿴ ...)
MATRIX_SURROUND_BAND = 0.28   # thickness of the enclosing band, as a fraction of the smaller side of the box
MATRIX_MIN_FONT_PT = 3.0      # no character is set smaller than this, however small its box
MATRIX_TAG_FONT_PT = 3.0      # the name of a composite (喿 in 藻) printed in the corner of its box
MATRIX_TAG_INSET = (0.03 / 4.4, 0.02 / 4.4)  # that label's distance from the corner (x, y), as fractions of the side
MATRIX_OVERLAY_OPACITY = 0.55  # the second layer of an overlay (⿻)

# ---- tree  (\zitree) -------------------------------------------------------------------------------------------
TREE_LEVEL_DX_CM = 2.4        # horizontal distance between a node and its children
TREE_LEAF_DY_CM = 0.85        # vertical distance between neighbouring leaves
TREE_NODE_MIN_CM = 0.65       # minimum height and width of a node
TREE_NODE_INNER_SEP_PT = 3.0
TREE_NODE_ROUNDING_PT = 1.5
TREE_NODE_FONT = r"\large"    # a node
TREE_ROOT_FONT = r"\LARGE\bfseries"  # the root (the character being decomposed)
TREE_ROOT_LINE_PT = 0.9
TREE_OP_FONT = r"\small"      # the operator printed after a named composite
TREE_OP_ALONE_FONT = r"\large"  # the operator of a node with no name
TREE_PATTERN_FONT = r"\scriptsize"  # a general pattern shown as an operator, such as LU-RU-M-LD-RD
TREE_POS_FONT = r"\tiny"      # the position label (L, M, RU ...) on an edge
TREE_POS_GAP_CM = 0.06        # that label's distance from its node
TREE_POS_INNER_SEP_PT = 1.0

# ---- equation  (\zimath) ---------------------------------------------------------------------------------------
MATH_FONT = r"\Large"         # the size of the whole equation (a TeX size command; "" keeps the document's size). Not used when wrap="none"

# ---- formula  (\ziformula): inline text, so it keeps the size of the sentence around it -----------------------------
FORMULA_INFO_FONT = r"\small"  # the "(pinyin, meaning)" after the formula
FORMULA_POS_FONT = r"\scriptsize"  # a position shown as a subscript, when positions are asked for

# ---- glyphs that need a fallback (see fonts.yaml) -------------------------------------------------------------
IMAGE_GLYPH_HEIGHT = "0.9em"  # an SVG or image glyph, as high as the text
IMAGE_GLYPH_RAISE = "-0.12em"  # and lowered a little, to sit on the baseline
MISSING_GLYPH_FONT = r"\scriptsize"  # the boxed U+XXXX label of a component nothing can draw

# ---- standalone PDFs (--emit pdf) ------------------------------------------------------------------------------
STANDALONE_BORDER_PT = 6

# ---- colours, as (R, G, B) -------------------------------------------------------------------------------------
PT_PER_CM = 28.4528           # a physical constant: TeX points in a cm
ROLE_FILL = {
    "semantic": (214, 234, 248),
    "phonetic": (252, 228, 214),
    "force": (226, 240, 217),
    "both": (232, 222, 245),      # a component that is both semantic and phonetic
}
DEFAULT_FILL = (248, 249, 250)
BORDER = (44, 62, 80)
ACCENT = (231, 76, 60)
MUTED = (127, 140, 141)
