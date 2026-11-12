from types import SimpleNamespace

import httpx
import pytest

from nextgram import aiogram_rich as AR
from nextgram import http_rich as HR
from nextgram import ptb_rich as PR


class _FakeResponse:
    def __init__(self, status_code=200, body=None):
        self.status_code = status_code
        self._body = {"ok": True, "result": {"message_id": 1}} if body is None else body

    def json(self):
        return self._body

    @property
    def text(self):
        return str(self._body)


class _FakeAsyncClient:
    def __init__(self, calls, responses, **kwargs):
        self._calls = calls
        self._responses = responses

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None):
        self._calls.append((url, json))
        if self._responses:
            return self._responses.pop(0)
        return _FakeResponse()


@pytest.fixture
def http(monkeypatch):
    calls = []
    responses = []
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kw: _FakeAsyncClient(calls, responses, **kw)
    )
    return SimpleNamespace(calls=calls, responses=responses)


class TestCoerceMarkupToDict:
    def test_none_passes_through(self):
        assert HR.coerce_markup_to_dict(None) is None

    def test_dict_passes_through_unchanged(self):
        markup = {"inline_keyboard": [[{"text": "Hi", "callback_data": "x"}]]}
        assert HR.coerce_markup_to_dict(markup) is markup

    def test_model_dump_style_object_is_converted(self):
        markup = SimpleNamespace(
            model_dump=lambda mode=None, exclude_none=None: {"inline_keyboard": []}
        )
        assert HR.coerce_markup_to_dict(markup) == {"inline_keyboard": []}

    def test_to_dict_style_object_is_converted(self):
        markup = SimpleNamespace(to_dict=lambda: {"inline_keyboard": [["a"]]})
        assert HR.coerce_markup_to_dict(markup) == {"inline_keyboard": [["a"]]}

    def test_unrecognized_object_passes_through_unchanged(self):
        markup = object()
        assert HR.coerce_markup_to_dict(markup) is markup


class TestSendRichHtmlViaHttp:
    async def test_plain_text_goes_straight_to_sendMessage(self, http):
        result = await HR.send_rich_html_via_http("123:ABC", 1, "hello")
        assert result == {"message_id": 1}
        assert len(http.calls) == 1
        url, payload = http.calls[0]
        assert url.endswith("/bot123:ABC/sendMessage")
        assert payload["text"] == "hello"
        assert payload["parse_mode"] == "HTML"

    async def test_rich_html_tries_sendRichMessage_first(self, http):
        result = await HR.send_rich_html_via_http("123:ABC", 1, "<h1>Hi</h1>")
        assert result == {"message_id": 1}
        assert len(http.calls) == 1
        url, payload = http.calls[0]
        assert url.endswith("/bot123:ABC/sendRichMessage")
        assert payload["rich_message"] == {"html": "<h1>Hi</h1>"}

    async def test_rich_rejection_falls_back_to_plain_sendMessage(self, http):
        http.responses.append(_FakeResponse(400, {"ok": False, "description": "nope"}))
        result = await HR.send_rich_html_via_http("123:ABC", 1, "<h1>Hi</h1>")
        assert result == {"message_id": 1}
        assert len(http.calls) == 2
        assert http.calls[0][0].endswith("sendRichMessage")
        assert http.calls[1][0].endswith("sendMessage")
        assert http.calls[1][1]["text"] == "<b>Hi</b>"

    async def test_markdown_uses_markdown_rich_message_and_parse_mode(self, http):
        await HR.send_rich_html_via_http("123:ABC", 1, "*bold*", markdown=True)
        _url, payload = http.calls[0]
        assert payload["rich_message"] == {"markdown": "*bold*"}

    async def test_empty_text_returns_none_without_a_call(self, http):
        assert await HR.send_rich_html_via_http("123:ABC", 1, "") is None
        assert http.calls == []

    async def test_reply_markup_and_thread_options_are_forwarded(self, http):
        await HR.send_rich_html_via_http(
            "123:ABC",
            1,
            "hello",
            reply_markup={"inline_keyboard": []},
            message_thread_id=7,
            disable_notification=True,
        )
        _url, payload = http.calls[0]
        assert payload["reply_markup"] == {"inline_keyboard": []}
        assert payload["message_thread_id"] == 7
        assert payload["disable_notification"] is True


class TestEditRichHtmlViaHttp:
    async def test_rich_edit_tries_editMessageText_with_rich_message(self, http):
        result = await HR.edit_rich_html_via_http("123:ABC", 1, 42, "<h1>Hi</h1>")
        assert result == {"message_id": 1}
        url, payload = http.calls[0]
        assert url.endswith("editMessageText")
        assert payload["rich_message"] == {"html": "<h1>Hi</h1>"}
        assert payload["message_id"] == 42

    async def test_rich_edit_rejection_falls_back_to_plain_edit(self, http):
        http.responses.append(_FakeResponse(400, {"ok": False, "description": "nope"}))
        result = await HR.edit_rich_html_via_http("123:ABC", 1, 42, "<h1>Hi</h1>")
        assert result == {"message_id": 1}
        assert len(http.calls) == 2
        assert "text" in http.calls[1][1]
        assert "rich_message" not in http.calls[1][1]

    async def test_empty_text_returns_none_without_a_call(self, http):
        assert await HR.edit_rich_html_via_http("123:ABC", 1, 42, "") is None
        assert http.calls == []


class TestAiogramRich:
    def test_aiogram_bot_token_reads_token_attribute(self):
        bot = SimpleNamespace(token="aio:TOKEN")
        assert AR.aiogram_bot_token(bot) == "aio:TOKEN"

    def test_aiogram_bot_token_without_token_raises(self):
        with pytest.raises(RuntimeError):
            AR.aiogram_bot_token(SimpleNamespace())

    async def test_aiogram_rich_send_calls_http_layer_with_resolved_token(self, http):
        bot = SimpleNamespace(token="aio:TOKEN")
        result = await AR.aiogram_rich_send(bot, 55, "hello")
        assert result == {"message_id": 1}
        url, payload = http.calls[0]
        assert "aio:TOKEN" in url
        assert payload["chat_id"] == 55

    async def test_aiogram_rich_reply_reads_bot_and_chat_from_message(self, http):
        message = SimpleNamespace(
            bot=SimpleNamespace(token="aio:TOKEN"),
            chat=SimpleNamespace(id=55),
            message_id=9,
        )
        result = await AR.aiogram_rich_reply(message, "hello")
        assert result == {"message_id": 1}
        _url, payload = http.calls[0]
        assert payload["chat_id"] == 55
        assert payload["reply_parameters"] == {"message_id": 9}

    async def test_aiogram_rich_reply_without_chat_returns_none(self):
        message = SimpleNamespace(bot=SimpleNamespace(token="aio:TOKEN"), chat=None)
        assert await AR.aiogram_rich_reply(message, "hello") is None

    async def test_aiogram_rich_edit_reads_chat_and_message_id(self, http):
        message = SimpleNamespace(
            bot=SimpleNamespace(token="aio:TOKEN"),
            chat=SimpleNamespace(id=55),
            message_id=9,
        )
        result = await AR.aiogram_rich_edit(message, "hello")
        assert result == {"message_id": 1}
        _url, payload = http.calls[0]
        assert payload["chat_id"] == 55
        assert payload["message_id"] == 9

    async def test_aiogram_rich_edit_with_explicit_ids_and_no_message(self, http):
        bot = SimpleNamespace(token="aio:TOKEN")
        result = await AR.aiogram_rich_edit(None, "hello", bot=bot, chat_id=1, message_id=2)
        assert result == {"message_id": 1}


class TestPtbRich:
    def test_ptb_bot_token_reads_token_attribute(self):
        bot = SimpleNamespace(token="ptb:TOKEN")
        assert PR.ptb_bot_token(bot) == "ptb:TOKEN"

    def test_ptb_bot_token_without_token_raises(self):
        with pytest.raises(RuntimeError):
            PR.ptb_bot_token(SimpleNamespace())

    async def test_ptb_rich_send_calls_http_layer_with_resolved_token(self, http):
        bot = SimpleNamespace(token="ptb:TOKEN")
        result = await PR.ptb_rich_send(bot, 77, "hello")
        assert result == {"message_id": 1}
        url, payload = http.calls[0]
        assert "ptb:TOKEN" in url
        assert payload["chat_id"] == 77

    async def test_ptb_rich_reply_reads_bot_and_chat_from_message(self, http):
        message = SimpleNamespace(
            get_bot=lambda: SimpleNamespace(token="ptb:TOKEN"),
            chat=SimpleNamespace(id=77),
            chat_id=77,
            message_id=3,
        )
        result = await PR.ptb_rich_reply(message, "hello")
        assert result == {"message_id": 1}
        _url, payload = http.calls[0]
        assert payload["chat_id"] == 77
        assert payload["reply_parameters"] == {"message_id": 3}

    async def test_ptb_rich_reply_accepts_an_update_via_effective_message(self, http):
        message = SimpleNamespace(
            get_bot=lambda: SimpleNamespace(token="ptb:TOKEN"),
            chat=SimpleNamespace(id=77),
            chat_id=77,
            message_id=3,
        )
        update = SimpleNamespace(effective_message=message)
        result = await PR.ptb_rich_reply(update, "hello")
        assert result == {"message_id": 1}

    async def test_ptb_rich_edit_with_explicit_ids_and_no_message(self, http):
        bot = SimpleNamespace(token="ptb:TOKEN")
        result = await PR.ptb_rich_edit(None, "hello", bot=bot, chat_id=1, message_id=2)
        assert result == {"message_id": 1}
