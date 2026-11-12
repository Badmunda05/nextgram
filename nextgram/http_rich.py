"""nextgram.http_rich: raw Bot HTTP API rich-message sending.

aiogram and python-telegram-bot have no MTProto layer at all — just a bot
token and the plain Bot HTTP API — so ``nextgram.aiogram_rich`` and
``nextgram.ptb_rich`` both build on this module instead of
``nextgram.rich_ui``'s Pyrogram-native path. Sending calls the same
``sendRichMessage`` HTTP endpoint ``nextgram.rich_ui._send_blocks_via_http``
already uses for typed blocks, this time with a plain ``{"html": ...}``
payload (the HTTP shape of ``InputRichMessage(html=...)``) instead of
``blocks``. This is a real, already-used endpoint, not a new guess.

Editing is less certain: there is no documented standalone
``editRichMessage`` HTTP method, only Pyrogram's native, MTProto-level
``edit_message_text(..., rich_message=...)``. :func:`edit_rich_html_via_http`
tries the same ``rich_message`` field on the plain HTTP ``editMessageText``
call — speculative, since it has never been confirmed against a live bot —
and falls back to a plain-HTML edit on any failure, exactly as the send
side falls back when ``sendRichMessage`` is rejected or unavailable.

Buttons built with ``rich_button()``/``rich_button_row()`` are embedded
*inside* the rich HTML and only become clickable when the rich payload is
actually accepted and rendered that way by the Telegram client — if a send
or edit falls back to plain HTML, those buttons degrade to plain text
labels (via ``rich_ui._plain_fallback``), exactly as they do on the
Pyrogram path when ``RICH_AVAILABLE`` is ``False``.
"""
from __future__ import annotations

import logging

from .rich_ui import _has_rich_only_tags, _normalize_html, _only_set, _plain_fallback
from .widgets import WidgetAPIError, _call_bot_api

logger = logging.getLogger("nextgram.http_rich")

__all__ = ["send_rich_html_via_http", "edit_rich_html_via_http", "coerce_markup_to_dict"]


def coerce_markup_to_dict(reply_markup):
    """Turn a framework-native keyboard object into a plain JSON-able dict.

    ``None``/dict pass through unchanged. aiogram v3's Pydantic models use
    ``.model_dump(mode="json", exclude_none=True)``; python-telegram-bot's
    use ``.to_dict()``; both are tried, in that order, before giving up and
    returning the object as-is (letting the eventual JSON encode fail
    loudly rather than silently dropping the keyboard).
    """
    if reply_markup is None or isinstance(reply_markup, dict):
        return reply_markup
    for method_name, kwargs in (
        ("model_dump", {"mode": "json", "exclude_none": True}),
        ("to_dict", {}),
    ):
        method = getattr(reply_markup, method_name, None)
        if callable(method):
            try:
                return method(**kwargs)
            except TypeError:
                try:
                    return method()
                except Exception:
                    continue
            except Exception:
                continue
    return reply_markup


async def send_rich_html_via_http(
    token,
    chat_id,
    html_text: str,
    *,
    markdown: bool = False,
    reply_markup: dict = None,
    reply_parameters: dict = None,
    message_thread_id=None,
    disable_notification=None,
    protect_content=None,
    api_base=None,
):
    """POST ``sendRichMessage``, falling back to plain ``sendMessage``.

    ``reply_markup``/``reply_parameters`` are plain JSON-able dicts (the
    Bot API wire shape) — a caller holding a framework-native keyboard
    object converts it first (aiogram: ``.model_dump(mode="json",
    exclude_none=True)``; python-telegram-bot: ``.to_dict()``).

    Returns the Bot API ``result`` dict (with ``message_id``) from
    whichever call succeeds, or ``None`` if both fail.
    """
    if not html_text:
        return None
    wants_rich = bool(markdown or _has_rich_only_tags(html_text))
    rich_message = (
        {"markdown": html_text} if markdown else {"html": _normalize_html(html_text)}
    )
    shared = _only_set(
        reply_markup=reply_markup,
        reply_parameters=reply_parameters,
        message_thread_id=message_thread_id,
        disable_notification=disable_notification,
        protect_content=protect_content,
    )
    if wants_rich:
        try:
            return await _call_bot_api(
                None,
                "sendRichMessage",
                {"chat_id": chat_id, "rich_message": rich_message, **shared},
                token=token,
                api_base=api_base,
            )
        except WidgetAPIError as e:
            logger.debug(f"[send_rich_html_via_http] rich send rejected, falling back: {e}")
        except Exception as e:
            logger.debug(f"[send_rich_html_via_http] rich send failed, falling back: {e}")

    try:
        return await _call_bot_api(
            None,
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": html_text if markdown else _plain_fallback(html_text),
                "parse_mode": "Markdown" if markdown else "HTML",
                **shared,
            },
            token=token,
            api_base=api_base,
        )
    except Exception as e:
        logger.debug(f"[send_rich_html_via_http] plain send failed: {e}")
        return None


async def edit_rich_html_via_http(
    token,
    chat_id,
    message_id,
    html_text: str,
    *,
    markdown: bool = False,
    reply_markup: dict = None,
    api_base=None,
):
    """POST ``editMessageText``, optimistically with ``rich_message`` set
    first (see the module docstring: unconfirmed, may always fall
    through), then a plain edit if that is rejected or fails outright.
    """
    if not html_text:
        return None
    wants_rich = bool(markdown or _has_rich_only_tags(html_text))
    rich_message = (
        {"markdown": html_text} if markdown else {"html": _normalize_html(html_text)}
    )
    shared = _only_set(reply_markup=reply_markup)
    if wants_rich:
        try:
            return await _call_bot_api(
                None,
                "editMessageText",
                {
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "rich_message": rich_message,
                    **shared,
                },
                token=token,
                api_base=api_base,
            )
        except Exception as e:
            logger.debug(f"[edit_rich_html_via_http] rich edit rejected, falling back: {e}")

    try:
        return await _call_bot_api(
            None,
            "editMessageText",
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": html_text if markdown else _plain_fallback(html_text),
                "parse_mode": "Markdown" if markdown else "HTML",
                **shared,
            },
            token=token,
            api_base=api_base,
        )
    except Exception as e:
        logger.debug(f"[edit_rich_html_via_http] plain edit failed: {e}")
        return None
