"""nextgram.aiogram_rich: rich messages and widgets for aiogram bots.

aiogram is optional — importing ``nextgram`` never requires it, and this
module has no import-time dependency on the ``aiogram`` package itself
(it only reads a few attributes off whatever ``Bot``/``Message`` objects
are passed in). Rich-message sending goes over the plain Bot HTTP API via
``nextgram.http_rich`` (see that module's docstring for exactly what is
confirmed vs. speculative); widgets go over the same HTTP API via
``nextgram.widgets``, which already works with any client exposing a
``.token`` attribute — aiogram's ``Bot`` does.
"""
from __future__ import annotations

import logging

from .http_rich import coerce_markup_to_dict, edit_rich_html_via_http, send_rich_html_via_http

logger = logging.getLogger("nextgram.aiogram_rich")

__all__ = [
    "aiogram_bot_token",
    "aiogram_rich_send",
    "aiogram_rich_reply",
    "aiogram_rich_edit",
]


def aiogram_bot_token(bot) -> str:
    """Pull the bot token off an aiogram ``Bot`` instance."""
    token = getattr(bot, "token", None)
    if not token:
        raise RuntimeError(
            "aiogram_bot_token needs a Bot instance with a .token attribute"
        )
    return token


async def aiogram_rich_send(
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
    """Send rich HTML/Markdown to ``chat_id`` with an aiogram ``Bot``.

    ``reply_markup`` accepts an aiogram ``InlineKeyboardMarkup`` (or any
    object with ``.model_dump``/``.to_dict``) as well as a plain dict.
    Returns the Bot API ``result`` dict (not an aiogram ``Message``) —
    use ``result["message_id"]`` for the sent message's id.
    """
    token = aiogram_bot_token(bot)
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


async def aiogram_rich_reply(message, html_text: str, *, bot=None, **kwargs):
    """Reply to an aiogram ``Message`` with rich HTML/Markdown.

    ``bot`` defaults to ``message.bot`` (aiogram sets this on every
    incoming message/update automatically).
    """
    app = bot or getattr(message, "bot", None)
    chat = getattr(getattr(message, "chat", None), "id", None)
    if app is None or chat is None:
        logger.debug("[aiogram_rich_reply] missing bot/chat on message")
        return None
    return await aiogram_rich_send(
        app, chat, html_text, reply_to_message_id=getattr(message, "message_id", None), **kwargs
    )


async def aiogram_rich_edit(
    message,
    html_text: str,
    *,
    bot=None,
    chat_id=None,
    message_id=None,
    markdown: bool = False,
    reply_markup=None,
):
    """Edit a message to rich HTML/Markdown with an aiogram ``Bot``.

    ``message`` is an aiogram ``Message`` (``.chat.id``/``.message_id``
    read automatically) or ``None``, in which case ``chat_id`` and
    ``message_id`` are required.
    """
    if message is not None:
        app = bot or getattr(message, "bot", None)
        chat_id = getattr(getattr(message, "chat", None), "id", None)
        message_id = getattr(message, "message_id", None)
    else:
        app = bot
    if app is None or chat_id is None or message_id is None:
        logger.debug("[aiogram_rich_edit] missing bot/chat_id/message_id")
        return None
    token = aiogram_bot_token(app)
    return await edit_rich_html_via_http(
        token,
        chat_id,
        message_id,
        html_text,
        markdown=markdown,
        reply_markup=coerce_markup_to_dict(reply_markup),
    )
