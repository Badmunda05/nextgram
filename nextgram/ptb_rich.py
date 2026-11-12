"""nextgram.ptb_rich: rich messages and widgets for python-telegram-bot bots.

python-telegram-bot is optional — importing ``nextgram`` never requires
it, and this module has no import-time dependency on the ``telegram``
package itself (it only reads a few attributes off whatever ``Bot``/
``Message`` objects are passed in). Rich-message sending goes over the
plain Bot HTTP API via ``nextgram.http_rich`` (see that module's docstring
for exactly what is confirmed vs. speculative); widgets go over the same
HTTP API via ``nextgram.widgets``, which already works with any client
exposing a ``.token`` attribute — python-telegram-bot's ``Bot`` does.
"""
from __future__ import annotations

import logging

from .http_rich import coerce_markup_to_dict, edit_rich_html_via_http, send_rich_html_via_http

logger = logging.getLogger("nextgram.ptb_rich")

__all__ = [
    "ptb_bot_token",
    "ptb_rich_send",
    "ptb_rich_reply",
    "ptb_rich_edit",
]


def ptb_bot_token(bot) -> str:
    """Pull the bot token off a python-telegram-bot ``Bot`` instance."""
    token = getattr(bot, "token", None)
    if not token:
        raise RuntimeError(
            "ptb_bot_token needs a Bot instance with a .token attribute"
        )
    return token


async def ptb_rich_send(
    bot,
    chat_id,
    html_text: str,
    *,
    markdown: bool = False,
    reply_markup=None,
    reply_to_message_id=None,
    message_thread_id=None,
    disable_notification=None,
    protect_content=None,
):
    """Send rich HTML/Markdown to ``chat_id`` with a python-telegram-bot
    ``Bot`` (or ``Bot``-like object — ``context.bot`` works the same way).

    ``reply_markup`` accepts a python-telegram-bot ``InlineKeyboardMarkup``
    (or any object with ``.to_dict``) as well as a plain dict. Returns the
    Bot API ``result`` dict (not a ``telegram.Message``) — use
    ``result["message_id"]`` for the sent message's id.
    """
    token = ptb_bot_token(bot)
    reply_parameters = (
        {"message_id": reply_to_message_id} if reply_to_message_id else None
    )
    return await send_rich_html_via_http(
        token,
        chat_id,
        html_text,
        markdown=markdown,
        reply_markup=coerce_markup_to_dict(reply_markup),
        reply_parameters=reply_parameters,
        message_thread_id=message_thread_id,
        disable_notification=disable_notification,
        protect_content=protect_content,
    )


async def ptb_rich_reply(message, html_text: str, *, bot=None, **kwargs):
    """Reply to a python-telegram-bot ``Message``/``Update`` with rich
    HTML/Markdown.

    Accepts either a ``telegram.Message`` or a ``telegram.Update`` (its
    ``.effective_message`` is used). ``bot`` defaults to
    ``message.get_bot()`` when the object exposes that (python-telegram-bot
    messages do).
    """
    target = getattr(message, "effective_message", None) or message
    app = bot
    if app is None:
        get_bot = getattr(target, "get_bot", None)
        app = get_bot() if callable(get_bot) else getattr(target, "_bot", None)
    chat = getattr(getattr(target, "chat", None), "id", None) or getattr(
        target, "chat_id", None
    )
    if app is None or chat is None:
        logger.debug("[ptb_rich_reply] missing bot/chat on message")
        return None
    return await ptb_rich_send(
        app, chat, html_text, reply_to_message_id=getattr(target, "message_id", None), **kwargs
    )


async def ptb_rich_edit(
    message,
    html_text: str,
    *,
    bot=None,
    chat_id=None,
    message_id=None,
    markdown: bool = False,
    reply_markup=None,
):
    """Edit a message to rich HTML/Markdown with a python-telegram-bot
    ``Bot``.

    ``message`` is a ``telegram.Message`` (``.chat_id``/``.message_id``
    read automatically) or ``None``, in which case ``chat_id`` and
    ``message_id`` are required.
    """
    if message is not None:
        if bot is None:
            get_bot = getattr(message, "get_bot", None)
            bot = get_bot() if callable(get_bot) else getattr(message, "_bot", None)
        chat_id = getattr(getattr(message, "chat", None), "id", None) or getattr(
            message, "chat_id", None
        )
        message_id = getattr(message, "message_id", None)
    app = bot
    if app is None or chat_id is None or message_id is None:
        logger.debug("[ptb_rich_edit] missing bot/chat_id/message_id")
        return None
    token = ptb_bot_token(app)
    return await edit_rich_html_via_http(
        token,
        chat_id,
        message_id,
        html_text,
        markdown=markdown,
        reply_markup=coerce_markup_to_dict(reply_markup),
    )
