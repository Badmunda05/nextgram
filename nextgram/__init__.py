"""NEXTGRAM: Telegram rich messages and HTML widgets."""

from . import rich_ui
from .rich_ui import *
from .rich_ui import __all__ as _rich_all

from . import widgets
from .widgets import *
from .widgets import __all__ as _widgets_all

__version__ = "0.9.1"

__all__ = list(_rich_all) + list(_widgets_all) + [
    "rich_ui",
    "widgets",
    "__version__",
]
