"""nextgram Telethon transport: Bot API 10.3 rich messages over MTProto."""
from __future__ import annotations

import inspect
import logging

from .rich_ui import (
    _has_rich_only_tags,
    _normalize_html,
    _only_set,
    _plain_fallback,
    _pre_segments,
    _todo_items,
)

logger = logging.getLogger("nextgram.telethon")

__all__ = [
    "TELETHON_RICH_AVAILABLE",
    "telethon_input_rich",
    "telethon_send_request",
    "telethon_edit_request",
    "telethon_block_paragraph",
    "telethon_block_details",
    "telethon_block_todo_list",
    "telethon_block_preformatted",
    "telethon_rich_send",
    "telethon_rich_send_blocks",
    "telethon_rich_reply",
    "telethon_rich_edit",
]


def _load_telethon():
    """Return Telethon's (types, functions), or raise RuntimeError."""
    try:
        from telethon import functions, types
    except ImportError as exc:
        raise RuntimeError(
            "Telethon support needs telethon installed: pip install nextgram[telethon]"
        ) from exc
    if not hasattr(types, "InputRichMessageHTML") or not hasattr(
        functions.messages, "SendMessageRequest"
    ):
        raise RuntimeError(
            "Telethon support needs a Telethon build with rich-message types "
            "(InputRichMessageHTML, SendMessageRequest with rich_message); "
            "telethon>=1.45 is known to work"
        )
    for name in ("SendMessageRequest", "EditMessageRequest"):
        request_cls = getattr(functions.messages, name, None)
        if request_cls is None:
            raise RuntimeError(
                f"Telethon support needs {name}; telethon>=1.45 is known to work"
            )
        try:
            params = inspect.signature(request_cls.__init__).parameters
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                f"Telethon support needs an inspectable {name} signature"
            ) from exc
        if "rich_message" not in params:
            raise RuntimeError(
                f"Telethon support needs {name} to accept rich_message — "
                "this Telethon build does not (stale wheel?); "
                "telethon>=1.45 is known to work"
            )
    return types, functions


try:
    _load_telethon()
    TELETHON_RICH_AVAILABLE = True
except RuntimeError:
    TELETHON_RICH_AVAILABLE = False


def _require_telethon():
    return _load_telethon()


def _is_flood_wait(error) -> bool:
    """True when the error is a Telethon rate-limit error."""
    try:
        from telethon.errors import FloodWaitError
    except ImportError:
        return False
    return isinstance(error, FloodWaitError)


async def _resolve_message(client, peer, result):
    """Return the real Message for a raw send/edit result, or None."""
    updates = getattr(result, "updates", None) or []
    for update in updates:
        message = getattr(update, "message", None)
        if message is not None:
            return message
    for update in updates:
        update_id = getattr(update, "id", None)
        if update_id is None:
            continue
        try:
            fetched = await client.get_messages(peer, ids=update_id)
        except Exception as e:
            logger.debug(f"[_resolve_message] fetch by id failed: {e}")
            continue
        if fetched is not None:
            return fetched
    return None


def telethon_input_rich(html_text: str, *, markdown: bool = False,
                        is_rtl=None, skip_entity_detection=None):
    """Build a Telethon ``InputRichMessage`` from HTML or Markdown text."""
    types, _functions = _require_telethon()
    if not html_text:
        raise ValueError("telethon_input_rich needs non-empty text")
    options = _only_set(is_rtl=is_rtl, skip_entity_detection=skip_entity_detection)
    if markdown:
        return types.InputRichMessageMarkdown(markdown=html_text, **options)
    return types.InputRichMessageHTML(html=_normalize_html(html_text), **options)


def _reply_header(reply_to_msg_id, top_msg_id):
    if reply_to_msg_id is None:
        return None
    types, _functions = _require_telethon()
    return types.InputReplyToMessage(
        reply_to_msg_id=int(reply_to_msg_id),
        top_msg_id=int(top_msg_id) if top_msg_id is not None else None,
    )


def telethon_send_request(peer, html_text: str, *, markdown: bool = False,
                         reply_to_msg_id=None, top_msg_id=None,
                         reply_markup=None, silent=None, no_webpage=None,
                         is_rtl=None, skip_entity_detection=None):
    """Build a raw ``messages.SendMessageRequest`` carrying a rich message."""
    _types, functions = _require_telethon()
    if not html_text:
        raise ValueError("telethon_send_request needs non-empty text")
    rich_message = telethon_input_rich(
        html_text, markdown=markdown, is_rtl=is_rtl,
        skip_entity_detection=skip_entity_detection,
    )
    companion = (
        html_text if markdown else _normalize_html(html_text)
    ) or " "
    return functions.messages.SendMessageRequest(
        peer=peer,
        message=companion,
        no_webpage=no_webpage,
        silent=silent,
        reply_to=_reply_header(reply_to_msg_id, top_msg_id),
        reply_markup=reply_markup,
        rich_message=rich_message,
    )


def telethon_edit_request(peer, message_id: int, html_text: str, *,
                         markdown: bool = False, reply_markup=None,
                         no_webpage=None, is_rtl=None,
                         skip_entity_detection=None):
    """Build a raw ``messages.EditMessageRequest`` carrying a rich message."""
    _types, functions = _require_telethon()
    if not html_text:
        raise ValueError("telethon_edit_request needs non-empty text")
    rich_message = telethon_input_rich(
        html_text, markdown=markdown, is_rtl=is_rtl,
        skip_entity_detection=skip_entity_detection,
    )
    companion = (
        html_text if markdown else _normalize_html(html_text)
    ) or " "
    return functions.messages.EditMessageRequest(
        peer=peer,
        id=int(message_id),
        message=companion,
        no_webpage=no_webpage,
        reply_markup=reply_markup,
        rich_message=rich_message,
    )


def telethon_block_paragraph(text: str):
    """A Telethon ``PageBlockParagraph`` for use in ``telethon_rich_send_blocks``."""
    types, _functions = _require_telethon()
    return types.PageBlockParagraph(text=text)


def telethon_block_details(title: str, blocks, open: bool = False):
    """A Telethon ``PageBlockDetails`` for use in ``telethon_rich_send_blocks``."""
    types, _functions = _require_telethon()
    if not isinstance(title, str) or not title.strip():
        raise ValueError("a details block needs a non-empty title string")
    return types.PageBlockDetails(
        blocks=list(blocks or ()),
        title=title,
        open=True if open else None,
    )


def telethon_block_todo_list(items):
    """A Telethon checklist block for use in ``telethon_rich_send_blocks``."""
    types, _functions = _require_telethon()
    return types.PageBlockList(
        items=[
            types.PageListItemText(text=text, checkbox=True, checked=done)
            for text, done in _todo_items(items)
        ]
    )


def telethon_block_preformatted(text, language: str = None):
    """A Telethon preformatted block with nested inline formatting."""
    types, _functions = _require_telethon()
    if language is not None and not isinstance(language, str):
        raise ValueError("a preformatted block's language must be a string")
    segments = _pre_segments(text)
    if isinstance(segments, str):
        rich_text = types.TextPlain(text=segments)
    else:
        parts = []
        for kind, value in segments:
            if kind == "rich":
                raise ValueError(
                    "Telethon preformatted blocks take (kind, text) segments, "
                    "not Kurigram RichText objects"
                )
            if kind == "bold":
                parts.append(types.TextBold(text=types.TextPlain(text=value)))
            elif kind == "italic":
                parts.append(types.TextItalic(text=types.TextPlain(text=value)))
            elif kind == "code":
                parts.append(types.TextFixed(text=types.TextPlain(text=value)))
            else:
                parts.append(types.TextPlain(text=value))
        rich_text = types.TextConcat(texts=parts)
    return types.PageBlockPreformatted(
        text=rich_text, language=language or ""
    )


async def telethon_rich_send_blocks(client, chat, blocks, *,
                                   reply_to_msg_id=None, top_msg_id=None,
                                   reply_markup=None, silent=None,
                                   no_webpage=None):
    """Send Telethon ``PageBlock`` objects as one rich message."""
    if not blocks:
        return None
    types, functions = _require_telethon()
    try:
        request = functions.messages.SendMessageRequest(
            peer=chat,
            message=" ",
            no_webpage=no_webpage,
            silent=silent,
            reply_to=_reply_header(reply_to_msg_id, top_msg_id),
            reply_markup=reply_markup,
            rich_message=types.InputRichMessage(blocks=list(blocks)),
        )
        result = await client(request)
        return await _resolve_message(client, chat, result)
    except Exception as e:
        if _is_flood_wait(e):
            raise
        logger.warning(f"[telethon_rich_send_blocks] block send failed: {e}")
        return None


async def telethon_rich_send(client, chat, html_text: str, *,
                            reply_to_msg_id=None, top_msg_id=None,
                            reply_markup=None, silent=None, no_webpage=None,
                            markdown: bool = False, is_rtl=None,
                            skip_entity_detection=None, **kwargs):
    """Send rich HTML/Markdown with a Telethon client, falling back to plain."""
    if not html_text:
        return None
    if kwargs:
        logger.debug(f"[telethon_rich_send] ignoring unknown arguments: {sorted(kwargs)}")

    wants_rich = bool(
        markdown or _has_rich_only_tags(html_text)
    )
    if TELETHON_RICH_AVAILABLE and wants_rich:
        try:
            request = telethon_send_request(
                chat, html_text, markdown=markdown,
                reply_to_msg_id=reply_to_msg_id, top_msg_id=top_msg_id,
                reply_markup=reply_markup, silent=silent, no_webpage=no_webpage,
                is_rtl=is_rtl, skip_entity_detection=skip_entity_detection,
            )
            result = await client(request)
            return await _resolve_message(client, chat, result)
        except Exception as e:
            if _is_flood_wait(e):
                raise
            logger.debug(f"[telethon_rich_send] rich delivery failed, falling back: {e}")

    try:
        return await client.send_message(
            chat,
            _plain_fallback(html_text) if not markdown else html_text,
            parse_mode="html" if not markdown else "md",
            reply_to=int(reply_to_msg_id) if reply_to_msg_id is not None else None,
            reply_markup=reply_markup,
            silent=silent,
            link_preview=False if no_webpage else None,
        )
    except Exception as e:
        if _is_flood_wait(e):
            raise
        logger.debug(f"[telethon_rich_send] plain send failed: {e}")
        return None


async def telethon_rich_reply(message, html_text: str, *, client=None,
                             **kwargs):
    """Reply to a Telethon message (or callback query) with rich text."""
    if not html_text:
        return None

    if hasattr(message, "data") and hasattr(message, "message"):
        inner = getattr(message, "message", None)
        chat = getattr(inner, "chat_id", None) if inner is not None else None
        reply_to = getattr(inner, "id", None) if inner is not None else None
        app = client or getattr(message, "client", None) or getattr(
            message, "_client", None
        )
    else:
        chat = getattr(message, "chat_id", None)
        reply_to = getattr(message, "id", None)
        app = (
            client or getattr(message, "client", None)
            or getattr(message, "_client", None)
        )
    if app is None or chat is None or reply_to is None:
        return None
    return await telethon_rich_send(
        app, chat, html_text, reply_to_msg_id=reply_to, **kwargs
    )


async def telethon_rich_edit(target, html_text: str, *, client=None,
                            chat=None, message_id=None, **kwargs):
    """Edit a message to rich text with a Telethon client."""
    if not html_text:
        return None

    if hasattr(target, "chat_id") and hasattr(target, "id"):
        app = client or getattr(target, "client", None) or getattr(
            target, "_client", None
        )
        chat = target.chat_id
        message_id = target.id
    else:
        app = client or target
    if app is None or chat is None or message_id is None:
        logger.debug("[telethon_rich_edit] missing client/chat/message_id")
        return None

    markdown = kwargs.pop("markdown", False)
    is_rtl = kwargs.pop("is_rtl", None)
    skip_entity_detection = kwargs.pop("skip_entity_detection", None)
    reply_markup = kwargs.pop("reply_markup", None)
    no_webpage = kwargs.pop("no_webpage", None)
    if kwargs:
        logger.debug(f"[telethon_rich_edit] ignoring unknown arguments: {sorted(kwargs)}")

    wants_rich = bool(markdown or _has_rich_only_tags(html_text))
    if TELETHON_RICH_AVAILABLE and wants_rich:
        try:
            request = telethon_edit_request(
                chat, message_id, html_text, markdown=markdown,
                reply_markup=reply_markup, no_webpage=no_webpage,
                is_rtl=is_rtl, skip_entity_detection=skip_entity_detection,
            )
            result = await app(request)
            return await _resolve_message(app, chat, result)
        except Exception as e:
            if _is_flood_wait(e):
                raise
            logger.debug(f"[telethon_rich_edit] rich edit failed, falling back: {e}")

    try:
        return await app.edit_message(
            chat,
            message_id,
            _plain_fallback(html_text) if not markdown else html_text,
            parse_mode="html" if not markdown else "md",
            reply_markup=reply_markup,
        )
    except Exception as e:
        if _is_flood_wait(e):
            raise
        logger.debug(f"[telethon_rich_edit] plain edit failed: {e}")
        return None
