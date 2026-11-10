from types import SimpleNamespace

import httpx
import pytest

from richgram import widgets as W


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


def client(token="123:ABC"):
    return SimpleNamespace(bot_token=token)


def test_widget_html_compressed_size_matches_zlib_level_9():
    import zlib

    html = "<div>" + "x" * 500 + "</div>"
    assert W.widget_html_compressed_size(html) == len(
        zlib.compress(html.encode("utf-8"), level=9)
    )


def test_validate_widget_html_rejects_empty():
    with pytest.raises(ValueError):
        W.validate_widget_html("")
    with pytest.raises(ValueError):
        W.validate_widget_html("   ")


def test_validate_widget_html_rejects_oversize():
    """Random-ish content compresses poorly, so this clears 4096 bytes easily."""
    import os

    big = "<div>" + os.urandom(6000).hex() + "</div>"
    with pytest.raises(ValueError, match="4096"):
        W.validate_widget_html(big)


def test_validate_widget_html_accepts_small_html():
    assert W.validate_widget_html("<b>hi</b>") == "<b>hi</b>"


def test_build_wallet_transaction_answer_bounds():
    with pytest.raises(ValueError):
        W.build_wallet_transaction_answer(1, [])
    with pytest.raises(ValueError):
        W.build_wallet_transaction_answer(1, [{"address": "a", "amount": 1}] * 256)


def test_build_wallet_transaction_answer_normalizes_amount():
    answer = W.build_wallet_transaction_answer(999, [{"address": "a", "amount": 1000}])
    assert answer == {"valid_until": 999, "messages": [{"address": "a", "amount": "1000"}]}


def test_build_wallet_transaction_answer_rejects_bad_amount():
    with pytest.raises(ValueError):
        W.build_wallet_transaction_answer(1, [{"address": "a", "amount": "not-a-number"}])
    with pytest.raises(ValueError):
        W.build_wallet_transaction_answer(1, [{"address": "a", "amount": -5}])


def test_build_wallet_transaction_answer_needs_address_and_amount():
    with pytest.raises(ValueError):
        W.build_wallet_transaction_answer(1, [{"amount": 1}])


def test_validate_nanoton_amount_accepts_int_and_digit_string():
    assert W.validate_nanoton_amount(5) == "5"
    assert W.validate_nanoton_amount("500") == "500"


def test_validate_nanoton_amount_rejects_bad_values():
    for bad in (-1, "abc", True, 1.5):
        with pytest.raises(ValueError):
            W.validate_nanoton_amount(bad)


def test_parse_widget_query_requires_fields():
    with pytest.raises(ValueError):
        W.parse_widget_query({"id": "1"})


def test_parse_widget_query_needs_exactly_one_addressing_form():
    base = {"id": "1", "from": {"id": 1}, "chat_instance": "ci", "widget_id": "w"}
    with pytest.raises(ValueError):
        W.parse_widget_query(dict(base))
    with pytest.raises(ValueError):
        W.parse_widget_query(
            dict(base, chat={"id": 2}, message_id=3, inline_message_id="im")
        )


def test_parse_widget_query_chat_message_form():
    wq = W.parse_widget_query(
        {
            "id": "wq1",
            "from": {"id": 7},
            "chat": {"id": 2},
            "message_id": 3,
            "chat_instance": "ci",
            "widget_id": "w1",
            "data": "hello",
        }
    )
    assert wq.id == "wq1"
    assert wq.chat == {"id": 2}
    assert wq.message_id == 3
    assert wq.inline_message_id is None
    assert wq.data == b"hello"
    assert wq.wallet is None


def test_parse_widget_query_inline_form():
    wq = W.parse_widget_query(
        {
            "id": "wq1",
            "from": {"id": 7},
            "inline_message_id": "im1",
            "chat_instance": "ci",
            "widget_id": "w1",
        }
    )
    assert wq.inline_message_id == "im1"
    assert wq.chat is None
    assert wq.data is None


@pytest.mark.parametrize(
    "type_payload,expected_cls",
    [
        ({"type": "data", "wallet_card": {"address": "a", "balance": "1"}}, W.WalletCard),
        (
            {"type": "sent_transaction", "wallet": {"address": "a"}, "msg_hash": "h"},
            W.WalletSentTransaction,
        ),
        ({"type": "sign_data", "signature": "s"}, W.WalletSignDataResult),
    ],
)
def test_parse_widget_query_wallet_payloads(type_payload, expected_cls):
    wq = W.parse_widget_query(
        {
            "id": "wq1",
            "from": {"id": 7},
            "chat": {"id": 2},
            "message_id": 3,
            "chat_instance": "ci",
            "widget_id": "w1",
            "type": type_payload,
        }
    )
    assert isinstance(wq.wallet, expected_cls)


def test_parse_widget_query_wallet_card_fields():
    wq = W.parse_widget_query(
        {
            "id": "wq1",
            "from": {"id": 7},
            "chat": {"id": 2},
            "message_id": 3,
            "chat_instance": "ci",
            "widget_id": "w1",
            "type": {"type": "data", "wallet_card": {"address": "EQabc", "balance": "42"}},
        }
    )
    assert wq.wallet.address == "EQabc"
    assert wq.wallet.balance == "42"


def test_parse_shared_widget_query_requires_fields():
    with pytest.raises(ValueError):
        W.parse_shared_widget_query({"id": "1"})


def test_parse_shared_widget_query_ok():
    swq = W.parse_shared_widget_query(
        {"id": "s1", "from": {"id": 9}, "widget_id": "w9", "data": "ping"}
    )
    assert swq.id == "s1"
    assert swq.widget_id == "w9"
    assert swq.data == b"ping"


def test_extract_widget_query_from_wrapped_update_dict():
    update = {
        "update_id": 1,
        "widget_query": {
            "id": "wq1",
            "from": {"id": 1},
            "chat": {"id": 2},
            "message_id": 3,
            "chat_instance": "ci",
            "widget_id": "w1",
        },
    }
    result = W.extract_widget_query(update)
    assert isinstance(result, W.WidgetQuery)


def test_extract_widget_query_from_wrapped_shared_update_dict():
    update = {
        "update_id": 1,
        "shared_widget_query": {"id": "s1", "from": {"id": 1}, "widget_id": "w1"},
    }
    result = W.extract_widget_query(update)
    assert isinstance(result, W.SharedWidgetQuery)


def test_extract_widget_query_from_bare_dict():
    assert isinstance(
        W.extract_widget_query(
            {
                "id": "wq1",
                "from": {"id": 1},
                "chat": {"id": 2},
                "message_id": 3,
                "chat_instance": "ci",
                "widget_id": "w1",
            }
        ),
        W.WidgetQuery,
    )
    assert isinstance(
        W.extract_widget_query({"id": "s1", "from": {"id": 1}, "widget_id": "w1"}),
        W.SharedWidgetQuery,
    )


def test_extract_widget_query_from_object_attribute():
    obj = SimpleNamespace(
        widget_query={
            "id": "wq1",
            "from": {"id": 1},
            "chat": {"id": 2},
            "message_id": 3,
            "chat_instance": "ci",
            "widget_id": "w1",
        }
    )
    assert isinstance(W.extract_widget_query(obj), W.WidgetQuery)


def test_extract_widget_query_returns_none_for_unrelated_update():
    assert W.extract_widget_query({"update_id": 1, "message": {}}) is None
    assert W.extract_widget_query(SimpleNamespace()) is None


def test_input_widget_message_content_validates_html():
    content = W.input_widget_message_content("<b>hi</b>", allow_queries=True)
    assert content == {"html": "<b>hi</b>", "allow_queries": True}
    with pytest.raises(ValueError):
        W.input_widget_message_content("")


def test_input_shared_widget_message_content_needs_id():
    assert W.input_shared_widget_message_content("w1") == {"widget_id": "w1"}
    with pytest.raises(ValueError):
        W.input_shared_widget_message_content("")


async def test_send_widget_calls_bot_api_and_returns_result(http):
    http.responses.append(_FakeResponse(200, {"ok": True, "result": {"message_id": 42}}))
    result = await W.send_widget(client(), 1, "<b>hi</b>", allow_queries=True)
    assert result == {"message_id": 42}
    url, payload = http.calls[0]
    assert url == "https://api.telegram.org/bot123:ABC/sendWidget"
    assert payload == {"chat_id": 1, "html": "<b>hi</b>", "allow_queries": True}


async def test_send_widget_needs_a_token(http):
    with pytest.raises(RuntimeError):
        await W.send_widget(SimpleNamespace(), 1, "<b>hi</b>")
    assert http.calls == []


async def test_send_widget_rejects_oversize_html_before_any_call(http):
    import os

    with pytest.raises(ValueError):
        await W.send_widget(client(), 1, "<div>" + os.urandom(6000).hex() + "</div>")
    assert http.calls == []


async def test_send_widget_raises_widget_api_error_on_failure(http):
    http.responses.append(
        _FakeResponse(400, {"ok": False, "error_code": 400, "description": "boom"})
    )
    with pytest.raises(W.WidgetAPIError) as exc_info:
        await W.send_widget(client(), 1, "<b>hi</b>")
    assert exc_info.value.error_code == 400
    assert "boom" in str(exc_info.value)


async def test_send_widget_prefers_native_client_method(http, monkeypatch):
    monkeypatch.setattr(W, "WIDGET_NATIVE_AVAILABLE", True)
    calls = []

    async def native(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(id=1)

    c = client()
    c.send_widget = native
    result = await W.send_widget(c, 1, "<b>hi</b>")
    assert calls and calls[0]["chat_id"] == 1
    assert http.calls == []
    assert result.id == 1


async def test_send_widget_falls_back_to_http_when_native_fails(http, monkeypatch):
    monkeypatch.setattr(W, "WIDGET_NATIVE_AVAILABLE", True)

    async def broken(**kwargs):
        raise RuntimeError("no native support yet")

    c = client()
    c.send_widget = broken
    http.responses.append(_FakeResponse(200, {"ok": True, "result": {"message_id": 5}}))
    result = await W.send_widget(c, 1, "<b>hi</b>")
    assert result == {"message_id": 5}
    assert len(http.calls) == 1


async def test_send_shared_widget_needs_widget_id(http):
    with pytest.raises(ValueError):
        await W.send_shared_widget(client(), 1, "")
    assert http.calls == []


async def test_send_shared_widget_calls_bot_api(http):
    http.responses.append(_FakeResponse(200, {"ok": True, "result": {"message_id": 9}}))
    result = await W.send_shared_widget(client(), 1, "w1", disable_notification=True)
    assert result == {"message_id": 9}
    url, payload = http.calls[0]
    assert url.endswith("/sendSharedWidget")
    assert payload == {"chat_id": 1, "widget_id": "w1", "disable_notification": True}


async def test_edit_message_widget_data_needs_exactly_one_addressing_form(http):
    with pytest.raises(ValueError):
        await W.edit_message_widget_data(client(), chat_data={"x": 1})
    with pytest.raises(ValueError):
        await W.edit_message_widget_data(
            client(), chat_id=1, message_id=2, inline_message_id="im", chat_data={"x": 1}
        )
    assert http.calls == []


async def test_edit_message_widget_data_needs_some_data(http):
    with pytest.raises(ValueError):
        await W.edit_message_widget_data(client(), chat_id=1, message_id=2)
    assert http.calls == []


async def test_edit_message_widget_data_by_chat_and_message(http):
    http.responses.append(_FakeResponse(200, {"ok": True, "result": True}))
    result = await W.edit_message_widget_data(
        client(), chat_id=1, message_id=2, public_data={"score": 10}
    )
    assert result is True
    url, payload = http.calls[0]
    assert url.endswith("/editMessageWidgetData")
    assert payload == {"chat_id": 1, "message_id": 2, "public_data": {"score": 10}}


async def test_edit_message_widget_data_by_inline_id(http):
    http.responses.append(_FakeResponse(200, {"ok": True, "result": True}))
    await W.edit_message_widget_data(
        client(), inline_message_id="im1", chat_data={"a": 1}
    )
    url, payload = http.calls[0]
    assert payload == {"inline_message_id": "im1", "chat_data": {"a": 1}}


async def test_edit_shared_widget_data_needs_widget_id(http):
    with pytest.raises(ValueError):
        await W.edit_shared_widget_data(client(), "")
    assert http.calls == []


@pytest.mark.parametrize("bad_cache_time", [4, 3601, -1, 2.5])
async def test_edit_shared_widget_data_validates_cache_time(http, bad_cache_time):
    with pytest.raises(ValueError):
        await W.edit_shared_widget_data(client(), "w1", cache_time=bad_cache_time)
    assert http.calls == []


async def test_edit_shared_widget_data_ok(http):
    http.responses.append(_FakeResponse(200, {"ok": True, "result": True}))
    await W.edit_shared_widget_data(client(), "w1", public_data={"n": 1}, cache_time=30)
    url, payload = http.calls[0]
    assert url.endswith("/editSharedWidgetData")
    assert payload == {"widget_id": "w1", "public_data": {"n": 1}, "cache_time": 30}


async def test_answer_widget_query_needs_an_id(http):
    with pytest.raises(ValueError):
        await W.answer_widget_query(client(), "")
    assert http.calls == []


async def test_answer_widget_query_validates_data_length(http):
    with pytest.raises(ValueError):
        await W.answer_widget_query(client(), "wq1", data="x" * 1025)
    assert http.calls == []


async def test_answer_widget_query_rejects_non_utf8_bytes(http):
    with pytest.raises(ValueError):
        await W.answer_widget_query(client(), "wq1", data=b"\xff\xfe")
    assert http.calls == []


async def test_answer_widget_query_enforces_15s_window():
    import time

    with pytest.raises(ValueError, match="15"):
        await W.answer_widget_query(
            client(), "wq1", received_at=time.time() - 20
        )


async def test_answer_widget_query_ok(http):
    http.responses.append(_FakeResponse(200, {"ok": True, "result": True}))
    result = await W.answer_widget_query(client(), "wq1", data="pong")
    assert result is True
    url, payload = http.calls[0]
    assert url.endswith("/answerWidgetQuery")
    assert payload == {"widget_query_id": "wq1", "data": "pong"}


async def test_answer_widget_query_without_data(http):
    http.responses.append(_FakeResponse(200, {"ok": True, "result": True}))
    await W.answer_widget_query(client(), "wq1")
    url, payload = http.calls[0]
    assert payload == {"widget_query_id": "wq1"}
