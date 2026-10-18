"""ZiNets-LaTeX: Chinese character decomposition trees, rendered through XeLaTeX."""
try:
    from importlib.metadata import version as _version
    __version__ = _version("zitex")
except Exception:          # not installed (running from a checkout)
    __version__ = "0.3.1"

from .ops import OPS, POSITIONS
from .tree import Node, ParseError, parse_shape, to_shape, node_from_dict, node_to_dict
from .loader import Entry, load_yaml
from .lexicon import Lexicon, load_lexicon
from .validate import Warn, validate_entry
from .fonts import FontConfig
from .render import render as render_snippet  # not named `render`: that would shadow the zitex.render module
from .render import render_with

__all__ = [
    "OPS", "POSITIONS", "Node", "ParseError", "parse_shape", "to_shape",
    "node_from_dict", "node_to_dict", "Entry", "load_yaml", "Lexicon", "load_lexicon", "FontConfig", "render_snippet", "render_with", "Warn", "validate_entry",
]
