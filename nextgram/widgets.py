"""nextgram.widgets: Bot API 10.4 HTML widgets."""
from __future__ import annotations

import logging
import time
import zlib
from dataclasses import dataclass, field
from typing import Any

from .rich_ui import _only_set

logger = logging.getLogger("nextgram.widgets")

__all__ = [
    "WIDGET_NATIVE_AVAILABLE",
    "WIDGET_HANDLER_NATIVE_AVAILABLE",
    "MAX_WIDGET_HTML_COMPRESSED_BYTES",
    "MAX_WIDGET_QUERY_REQUEST_BYTES",
    "MAX_WIDGET_ANSWER_DATA_BYTES",
    "MIN_WIDGET_CACHE_TIME",
    "MAX_WIDGET_CACHE_TIME",
    "MAX_WALLET_MESSAGES",
    "WidgetAPIError",
    "WalletCard",
    "WalletSentTransaction",
    "WalletSignDataResult",
    "WidgetQuery",
    "SharedWidgetQuery",
    "Widget",
    "widget_html_compressed_size",
    "validate_widget_html",
    "validate_nanoton_amount",
    "parse_widget_query",
    "parse_shared_widget_query",
    "extract_widget_query",
    "parse_widget",
    "extract_widget",
    "build_wallet_transaction_answer",
    "send_widget",
    "send_shared_widget",
    "edit_message_widget_data",
    "edit_shared_widget_data",
    "answer_widget_query",
    "input_widget_message_content",
    "input_shared_widget_message_content",
    "register_widget_query_handler",
]

try:
    from pyrogram import Client as _Client

    WIDGET_NATIVE_AVAILABLE = hasattr(_Client, "send_widget")
except Exception:
    WIDGET_NATIVE_AVAILABLE = False

try:
    from pyrogram import handlers as _handlers

    WIDGET_HANDLER_NATIVE_AVAILABLE = hasattr(_handlers, "WidgetQueryHandler") and hasattr(
        _handlers, "SharedWidgetQueryHandler"
    )
except Exception:
    WIDGET_HANDLER_NATIVE_AVAILABLE = False
"""WIDGET_HANDLER_NATIVE_AVAILABLE: whether the installed pyrogram-family package (Pyrogram, Pyrofork or Kurigram - one family, same ``pyrogram`` import name)…"""


_LIMITS_DOC = """Documented limits (core.telegram.org/bots/widgets):

MAX_WIDGET_HTML_COMPRESSED_BYTES: the zlib level-9 compressed size limit
for a widget's HTML source.

MAX_WIDGET_QUERY_REQUEST_BYTES: the widget JS side's
``TelegramWidget.request(data)`` sends 1-64 bytes; kept here for
documentation/validation of fixtures, since nextgram (server side) never
constructs this payload itself.

MAX_WIDGET_ANSWER_DATA_BYTES: ``answerWidgetQuery``'s optional ``data`` is
at most 1024 bytes.

ANSWER_WIDGET_QUERY_WINDOW_SECONDS: ``answerWidgetQuery`` must be called
within this many seconds of receiving the query.

MIN_WIDGET_CACHE_TIME / MAX_WIDGET_CACHE_TIME: ``editSharedWidgetData``'s
``cache_time`` bounds, in seconds.

MAX_WALLET_MESSAGES: a wallet transaction answer carries 1-255 messages.
"""

MAX_WIDGET_HTML_COMPRESSED_BYTES = 4096
MAX_WIDGET_QUERY_REQUEST_BYTES = 64
MAX_WIDGET_ANSWER_DATA_BYTES = 1024
ANSWER_WIDGET_QUERY_WINDOW_SECONDS = 15
MIN_WIDGET_CACHE_TIME = 5
MAX_WIDGET_CACHE_TIME = 3600
MAX_WALLET_MESSAGES = 255

_DEFAULT_BOT_API_BASE = "https://api.telegram.org"


class WidgetAPIError(RuntimeError):
    """Raised when the Bot HTTP API rejects a widget call (``ok: false``)."""

    def __init__(self, method: str, status_code: int, payload: dict):
        self.method = method
        self.status_code = status_code
        self.payload = payload or {}
        self.error_code = self.payload.get("error_code")
        self.description = self.payload.get("description", "")
        super().__init__(
            f"{method} failed ({status_code}"
            + (f", error_code={self.error_code}" if self.error_code else "")
            + f"): {self.description or payload}"
        )




def widget_html_compressed_size(html_text: str) -> int:
    """The size the widgets guide checks the 4096-byte limit against."""
    return len(zlib.compress(str(html_text).encode("utf-8"), level=9))


def validate_widget_html(html_text: str) -> str:
    if not isinstance(html_text, str) or not html_text.strip():
        raise ValueError("a widget needs non-empty HTML source")
    size = widget_html_compressed_size(html_text)
    if size > MAX_WIDGET_HTML_COMPRESSED_BYTES:
        raise ValueError(
            f"widget HTML is {size} bytes compressed (zlib level 9), "
            f"over the {MAX_WIDGET_HTML_COMPRESSED_BYTES}-byte limit"
        )
    return html_text


def _validate_answer_data(data) -> str | None:
    """Validate and normalize ``answerWidgetQuery``'s ``data`` to ``str``."""
    if data is None:
        return None
    if isinstance(data, (bytes, bytearray)):
        try:
            data = bytes(data).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(
                "answerWidgetQuery data must be UTF-8 text (Bot API JSON has "
                "no raw-byte field); encode non-UTF-8 payloads yourself "
                "(e.g. base64) before passing them as a str"
            ) from exc
    if not isinstance(data, str):
        raise ValueError("answerWidgetQuery data must be str or UTF-8 bytes")
    size = len(data.encode("utf-8"))
    if size > MAX_WIDGET_ANSWER_DATA_BYTES:
        raise ValueError(
            f"answerWidgetQuery data is {size} bytes, over the "
            f"{MAX_WIDGET_ANSWER_DATA_BYTES}-byte limit"
        )
    return data


def _validate_cache_time(cache_time) -> int | None:
    if cache_time is None:
        return None
    if isinstance(cache_time, bool) or not isinstance(cache_time, int):
        raise ValueError("cache_time must be an integer number of seconds")
    if not (MIN_WIDGET_CACHE_TIME <= cache_time <= MAX_WIDGET_CACHE_TIME):
        raise ValueError(
            f"cache_time must be {MIN_WIDGET_CACHE_TIME}-"
            f"{MAX_WIDGET_CACHE_TIME} seconds, got {cache_time}"
        )
    return cache_time


def validate_nanoton_amount(amount) -> str:
    """Validate a wallet message's ``amount``: a decimal nanoton string."""
    if isinstance(amount, bool):
        raise ValueError("a wallet message amount must be a non-negative integer or digit string")
    if isinstance(amount, int):
        if amount < 0:
            raise ValueError("a wallet message amount must be non-negative")
        return str(amount)
    if isinstance(amount, str) and amount.isdigit():
        return amount
    raise ValueError(
        f"invalid nanoton amount {amount!r}: expected a non-negative integer "
        "or a decimal digit string"
    )




@dataclass(frozen=True)
class WalletCard:
    """``widget_query`` payload of ``type: "data"`` — a wallet info share."""

    raw: dict = field(default_factory=dict)

    @property
    def address(self):
        return self.raw.get("address")

    @property
    def balance(self):
        return self.raw.get("balance")


@dataclass(frozen=True)
class WalletSentTransaction:
    """``widget_query`` payload of ``type: "sent_transaction"``."""

    wallet: Any
    msg_hash: str
    raw: dict = field(default_factory=dict)


@dataclass(frozen=True)
class WalletSignDataResult:
    """``widget_query`` payload of ``type: "sign_data"``."""

    raw: dict = field(default_factory=dict)


def _parse_wallet_payload(type_data: dict | None):
    if not type_data:
        return None
    kind = type_data.get("type")
    if kind == "data":
        return WalletCard(raw=dict(type_data.get("wallet_card") or {}))
    if kind == "sent_transaction":
        return WalletSentTransaction(
            wallet=type_data.get("wallet"),
            msg_hash=type_data.get("msg_hash"),
            raw=dict(type_data),
        )
    if kind == "sign_data":
        return WalletSignDataResult(raw=dict(type_data))
    return None


@dataclass(frozen=True)
class WidgetQuery:
    """A ``widget_query`` update: a request from a widget's own (non-shared) message, parsed from the raw Bot-API-JSON ``dict`` Telegram sends."""

    id: str
    from_user: dict
    chat_instance: str
    widget_id: str
    data: bytes | None
    chat: dict | None = None
    message_id: int | None = None
    inline_message_id: str | None = None
    chat_type: str | None = None
    wallet: WalletCard | WalletSentTransaction | WalletSignDataResult | None = None
    raw: dict = field(default_factory=dict)


@dataclass(frozen=True)
class SharedWidgetQuery:
    """A ``shared_widget_query`` update: a request from a forward of a shared widget."""

    id: str
    from_user: dict
    widget_id: str
    data: bytes | None
    raw: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Widget:
    """A widget attached to a message (``message["widget"]`` in Bot API JSON) — what you get back after :func:`send_widget`/ :func:`send_shared_widget`, or on any…"""

    html: str
    id: str | None = None
    width: int | None = None
    height: int | None = None
    public_data: str | None = None
    chat_data: str | None = None
    raw: dict = field(default_factory=dict)


def parse_widget(data: dict) -> Widget:
    """Parse one raw ``widget`` dict (a message's ``widget`` field) into a :class:`Widget`."""
    if not isinstance(data, dict):
        raise ValueError("parse_widget needs a dict (the widget object)")
    if "html" not in data:
        raise ValueError("widget is missing required field: 'html'")
    return Widget(
        html=data["html"],
        id=data.get("id"),
        width=data.get("width"),
        height=data.get("height"),
        public_data=data.get("public_data"),
        chat_data=data.get("chat_data"),
        raw=dict(data),
    )


def extract_widget(message) -> Widget | None:
    """Duck-type a message into its :class:`Widget`, or ``None``."""
    if isinstance(message, dict):
        if "widget" in message:
            widget = message["widget"]
            return parse_widget(widget) if widget else None
        if "html" in message:
            return parse_widget(message)
        return None

    widget = getattr(message, "widget", None)
    if widget is None:
        return None
    if isinstance(widget, dict):
        return parse_widget(widget)
    if isinstance(widget, Widget):
        return widget
    return Widget(
        html=getattr(widget, "html"),
        id=getattr(widget, "id", None),
        width=getattr(widget, "width", None),
        height=getattr(widget, "height", None),
        public_data=getattr(widget, "public_data", None),
        chat_data=getattr(widget, "chat_data", None),
        raw=vars(widget) if hasattr(widget, "__dict__") else {},
    )


def _decode_query_data(value):
    """Normalize an incoming query's ``data`` field to ``bytes``."""
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if isinstance(value, str):
        return value.encode("utf-8")
    raise ValueError(f"unexpected widget query data type: {type(value).__name__}")


def parse_widget_query(data: dict) -> WidgetQuery:
    """Parse one raw ``widget_query`` update dict into a :class:`WidgetQuery`."""
    if not isinstance(data, dict):
        raise ValueError("parse_widget_query needs a dict (the widget_query object)")
    required = ("id", "from", "chat_instance", "widget_id")
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"widget_query is missing required field(s): {missing}")
    chat = data.get("chat")
    message_id = data.get("message_id")
    inline_message_id = data.get("inline_message_id")
    if bool(chat and message_id is not None) == bool(inline_message_id):
        raise ValueError(
            "widget_query must carry exactly one of (chat + message_id) or "
            "inline_message_id"
        )
    return WidgetQuery(
        id=data["id"],
        from_user=dict(data["from"]),
        chat_instance=data["chat_instance"],
        widget_id=data["widget_id"],
        data=_decode_query_data(data.get("data")),
        chat=dict(chat) if chat else None,
        message_id=message_id,
        inline_message_id=inline_message_id,
        chat_type=data.get("chat_type"),
        wallet=_parse_wallet_payload(
            data.get("type") if isinstance(data.get("type"), dict) else None
        ),
        raw=dict(data),
    )


def parse_shared_widget_query(data: dict) -> SharedWidgetQuery:
    """Parse one raw ``shared_widget_query`` update dict."""
    if not isinstance(data, dict):
        raise ValueError("parse_shared_widget_query needs a dict (the shared_widget_query object)")
    required = ("id", "from", "widget_id")
    missing = [k for k in required if k not in data]
    if missing:
        raise ValueError(f"shared_widget_query is missing required field(s): {missing}")
    return SharedWidgetQuery(
        id=data["id"],
        from_user=dict(data["from"]),
        widget_id=data["widget_id"],
        data=_decode_query_data(data.get("data")),
        raw=dict(data),
    )


def extract_widget_query(update):
    """Duck-type an incoming update into a parsed widget query, or ``None``."""
    if isinstance(update, dict):
        if "widget_query" in update:
            return parse_widget_query(update["widget_query"])
        if "shared_widget_query" in update:
            return parse_shared_widget_query(update["shared_widget_query"])
        if {"id", "from", "widget_id"} <= set(update):
            if "chat_instance" in update:
                return parse_widget_query(update)
            return parse_shared_widget_query(update)
        return None

    wq = getattr(update, "widget_query", None)
    if wq is not None:
        return parse_widget_query(wq if isinstance(wq, dict) else vars(wq))
    swq = getattr(update, "shared_widget_query", None)
    if swq is not None:
        return parse_shared_widget_query(swq if isinstance(swq, dict) else vars(swq))
    return None


def build_wallet_transaction_answer(valid_until, messages) -> dict:
    """Build the bot's TON Connect-shaped transaction answer."""
    messages = list(messages or ())
    if not (1 <= len(messages) <= MAX_WALLET_MESSAGES):
        raise ValueError(
            f"a wallet transaction answer needs 1-{MAX_WALLET_MESSAGES} messages, "
            f"got {len(messages)}"
        )
    built = []
    for i, msg in enumerate(messages):
        if not isinstance(msg, dict) or "address" not in msg or "amount" not in msg:
            raise ValueError(f"wallet message #{i} needs at least 'address' and 'amount'")
        built.append(
            _only_set(
                address=msg["address"],
                amount=validate_nanoton_amount(msg["amount"]),
                payload=msg.get("payload"),
                stateInit=msg.get("stateInit"),
            )
        )
    return {"valid_until": int(valid_until), "messages": built}




def input_widget_message_content(html_text: str, *, allow_queries=None, is_shared=None,
                                  width=None, height=None) -> dict:
    """An ``InputWidgetMessageContent`` dict for ``answerInlineQuery``."""
    validate_widget_html(html_text)
    return _only_set(
        html=html_text,
        allow_queries=allow_queries,
        is_shared=is_shared,
        width=width,
        height=height,
    )


def input_shared_widget_message_content(widget_id: str) -> dict:
    """An ``InputSharedWidgetMessageContent`` dict for ``answerInlineQuery``."""
    if not widget_id:
        raise ValueError("input_shared_widget_message_content needs widget_id")
    return {"widget_id": widget_id}




def _resolve_token(client, token):
    """Widgets always go over the plain Bot HTTP API, so all this needs is a bot token string — it has no dependency on which framework's client object is passed…"""
    if token:
        return token
    for attr in ("bot_token", "token", "_bot_token"):
        value = getattr(client, attr, None)
        if isinstance(value, str) and value:
            return value
    raise RuntimeError(
        "widget methods need a bot token: pass token=..., or use a client "
        "that exposes one as .bot_token or .token (Pyrogram/Pyrofork/"
        "Kurigram, aiogram and python-telegram-bot all do; Telethon does "
        "not, so pass token=... explicitly for it)"
    )


async def _call_bot_api(client, method: str, payload: dict, *, token=None, api_base=None):
    """POST one Bot HTTP API method and return its ``result``."""
    import httpx

    resolved_token = _resolve_token(client, token)
    base = api_base or _DEFAULT_BOT_API_BASE
    endpoint = f"{base}/bot{resolved_token}/{method}"
    async with httpx.AsyncClient(timeout=15.0) as http_client:
        resp = await http_client.post(endpoint, json=payload)
    try:
        body = resp.json()
    except Exception:
        body = {}
    if resp.status_code != 200 or not body.get("ok"):
        raise WidgetAPIError(method, resp.status_code, body)
    return body.get("result")


async def _try_native(client, method_name, kwargs) -> tuple[bool, Any]:
    """Call ``client.<method_name>(**kwargs)`` if the client has it natively."""
    method = getattr(client, method_name, None) if WIDGET_NATIVE_AVAILABLE else None
    if method is None:
        return False, None
    try:
        return True, await method(**kwargs)
    except Exception as e:
        logger.debug(f"[widgets] native {method_name} failed, falling back to HTTP: {e}")
        return False, None




async def send_widget(
    client,
    chat_id,
    html_text: str,
    *,
    allow_queries: bool = None,
    is_shared: bool = None,
    width: int = None,
    height: int = None,
    reply_markup=None,
    reply_parameters=None,
    message_thread_id=None,
    business_connection_id=None,
    disable_notification=None,
    protect_content=None,
    token=None,
    api_base=None,
):
    """Send a new widget (``sendWidget``)."""
    validate_widget_html(html_text)
    kwargs = _only_set(
        chat_id=chat_id,
        html=html_text,
        allow_queries=allow_queries,
        is_shared=is_shared,
        width=width,
        height=height,
        reply_markup=reply_markup,
        reply_parameters=reply_parameters,
        message_thread_id=message_thread_id,
        business_connection_id=business_connection_id,
        disable_notification=disable_notification,
        protect_content=protect_content,
    )
    ok, result = await _try_native(client, "send_widget", kwargs)
    if ok:
        return result
    return await _call_bot_api(client, "sendWidget", kwargs, token=token, api_base=api_base)


async def send_shared_widget(
    client,
    chat_id,
    widget_id: str,
    *,
    reply_markup=None,
    reply_parameters=None,
    message_thread_id=None,
    business_connection_id=None,
    disable_notification=None,
    protect_content=None,
    token=None,
    api_base=None,
):
    """Re-send an existing shared widget by id (``sendSharedWidget``) — "the way a photo is sent again by its file_id", per the guide."""
    if not widget_id:
        raise ValueError("send_shared_widget needs a widget_id")
    kwargs = _only_set(
        chat_id=chat_id,
        widget_id=widget_id,
        reply_markup=reply_markup,
        reply_parameters=reply_parameters,
        message_thread_id=message_thread_id,
        business_connection_id=business_connection_id,
        disable_notification=disable_notification,
        protect_content=protect_content,
    )
    ok, result = await _try_native(client, "send_shared_widget", kwargs)
    if ok:
        return result
    return await _call_bot_api(client, "sendSharedWidget", kwargs, token=token, api_base=api_base)


async def edit_message_widget_data(
    client,
    *,
    chat_id=None,
    message_id=None,
    inline_message_id=None,
    chat_data=None,
    public_data=None,
    token=None,
    api_base=None,
):
    """Edit a static widget message's state (``editMessageWidgetData``)."""
    has_chat_addr = chat_id is not None and message_id is not None
    if bool(has_chat_addr) == bool(inline_message_id):
        raise ValueError(
            "edit_message_widget_data needs exactly one of "
            "(chat_id + message_id) or inline_message_id"
        )
    if chat_data is None and public_data is None:
        raise ValueError("edit_message_widget_data needs chat_data and/or public_data")
    kwargs = _only_set(
        chat_id=chat_id,
        message_id=message_id,
        inline_message_id=inline_message_id,
        chat_data=chat_data,
        public_data=public_data,
    )
    ok, result = await _try_native(client, "edit_message_widget_data", kwargs)
    if ok:
        return result
    return await _call_bot_api(
        client, "editMessageWidgetData", kwargs, token=token, api_base=api_base
    )


async def edit_shared_widget_data(
    client,
    widget_id: str,
    *,
    public_data=None,
    cache_time: int = None,
    token=None,
    api_base=None,
):
    """Edit a shared widget's state for every viewer (``editSharedWidgetData``)."""
    if not widget_id:
        raise ValueError("edit_shared_widget_data needs a widget_id")
    cache_time = _validate_cache_time(cache_time)
    kwargs = _only_set(widget_id=widget_id, public_data=public_data, cache_time=cache_time)
    ok, result = await _try_native(client, "edit_shared_widget_data", kwargs)
    if ok:
        return result
    return await _call_bot_api(
        client, "editSharedWidgetData", kwargs, token=token, api_base=api_base
    )


async def answer_widget_query(
    client,
    widget_query_id: str,
    data=None,
    *,
    received_at: float = None,
    token=None,
    api_base=None,
):
    """Answer a ``widget_query`` (``answerWidgetQuery``)."""
    if not widget_query_id:
        raise ValueError("answer_widget_query needs a widget_query_id")
    answer_data = _validate_answer_data(data)
    if received_at is not None:
        elapsed = time.time() - received_at
        if elapsed > ANSWER_WIDGET_QUERY_WINDOW_SECONDS:
            raise ValueError(
                f"answerWidgetQuery must be called within "
                f"{ANSWER_WIDGET_QUERY_WINDOW_SECONDS}s of receiving the query "
                f"({elapsed:.1f}s elapsed)"
            )
    kwargs = _only_set(widget_query_id=widget_query_id, data=answer_data)
    ok, result = await _try_native(client, "answer_widget_query", kwargs)
    if ok:
        return result
    return await _call_bot_api(client, "answerWidgetQuery", kwargs, token=token, api_base=api_base)




def register_widget_query_handler(client, callback, *, shared: bool = False, filters=None, group: int = 0):
    """Register ``callback`` for incoming ``widget_query`` (or, with ``shared=True``, ``shared_widget_query``) updates, the same way…"""
    if WIDGET_HANDLER_NATIVE_AVAILABLE and hasattr(client, "add_handler"):
        from pyrogram import handlers as _handlers

        handler_cls = _handlers.SharedWidgetQueryHandler if shared else _handlers.WidgetQueryHandler
        handler = handler_cls(callback, filters)
        client.add_handler(handler, group)
        return handler
    kind = "shared_widget_query" if shared else "widget_query"
    raise NotImplementedError(
        f"this client has no native {kind} dispatch yet (only Pyrogram/"
        "Pyrofork/Kurigram ship WidgetQueryHandler/SharedWidgetQueryHandler "
        "so far) - poll getUpdates (or your webhook handler) yourself and "
        f"pass each update through nextgram.widgets.extract_widget_query() "
        "to get the same typed object"
    )
