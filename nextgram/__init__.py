"""nextgram: Telegram Bot API 10.3 rich messages and Bot API 10.4 HTML
widgets, across six frameworks.

Pyrogram, Pyrofork and Kurigram are one family (three distributions of
the same ``pyrogram`` package name) and get full native support here, in
``nextgram.rich_ui`` — importing ``nextgram`` itself needs none of them
installed. Telethon, aiogram and python-telegram-bot are each supported
through their own optional module, imported explicitly so a bot using
only one framework never has to install the others:

- ``nextgram.telethon`` — ``from nextgram import telethon``
- ``nextgram.aiogram_rich`` — ``from nextgram import aiogram_rich``
- ``nextgram.ptb_rich`` — ``from nextgram import ptb_rich``

``nextgram.widgets`` (Bot API 10.4 widgets) is framework-agnostic by
construction — it only ever needs a bot token — so every function in it
already works the same from all six frameworks without a separate module
per framework; see its own docstring.

The content builders (``rich_heading``, ``rich_list``, ``rich_button``,
``rich_table``, ...) are plain string functions with no framework
dependency at all — the same HTML works everywhere; only how it gets
*sent* differs per framework, which is what the modules above are for.
"""

from . import rich_ui
from .rich_ui import *
from .rich_ui import __all__ as _rich_all
from . import widgets
from .widgets import *
from .widgets import __all__ as _widgets_all

__version__ = "0.9.0"
__all__ = list(_rich_all) + list(_widgets_all) + ["rich_ui", "widgets", "__version__"]
