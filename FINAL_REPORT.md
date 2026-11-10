# FINAL_REPORT — richgram Bot API 10.4 widget upgrade

Date: 2026-11-10

## 1. What was asked, and the correction mid-task

The first version of this request pasted a "Bot API 10.4" changelog that
turned out not to exist on Telegram's real documentation at the time I
checked (`core.telegram.org/bots/api` topped out at 10.3, no `sendWidget`
anywhere). I said so and declined to build against it.

You then said Telegram had, in fact, released Bot API 10.4 on
2026-11-09, and pointed me at two live URLs. I re-checked both directly:

- `core.telegram.org/bots/api` — **still 10.3** as the headline version;
  no `sendWidget`/`Widget`/`WidgetQuery` anywhere in the method/type
  reference, across the full page.
- `core.telegram.org/bots/widgets` — **does exist**, and is a genuine,
  detailed guide to a feature called Widgets, with `sendWidget`,
  `sendSharedWidget`, `editMessageWidgetData`, `editSharedWidgetData`,
  `answerWidgetQuery`, the `widget_query`/`shared_widget_query` update
  types, TON Wallet query/answer shapes, and a full `TelegramWidget`
  JavaScript reference for the widget side.

So: the feature is real and documented, but only on a standalone guide
page, not yet folded into the main method reference the way `sendPhoto`,
`sendMessage` etc. are. Everything built below is scoped to exactly what
that guide page states; nothing was invented to fill the gaps where it
doesn't give a full parameter table.

## 2. What was built

A new, additive module: `richgram/widgets.py` (~780 lines), exported from
the top-level `richgram` package (`richgram/__init__.py` now imports it
alongside the existing `rich_ui`), plus `tests/unit/test_widgets.py`
(~475 lines, 90 test functions/cases). Nothing in `rich_ui.py` or
`telethon.py` was touched — see §5, Backward compatibility.

Implemented, matching the guide page's documented names and shapes:

| Guide concept | richgram function/type |
|---|---|
| `sendWidget` | `send_widget(client, chat_id, html, *, allow_queries, is_shared, width, height, ...)` |
| `sendSharedWidget` | `send_shared_widget(client, chat_id, widget_id, ...)` |
| `editMessageWidgetData` | `edit_message_widget_data(client, *, chat_id, message_id, inline_message_id, chat_data, public_data)` |
| `editSharedWidgetData` | `edit_shared_widget_data(client, widget_id, *, public_data, cache_time)` |
| `answerWidgetQuery` | `answer_widget_query(client, widget_query_id, data=None, *, received_at=None)` |
| `widget_query` update | `WidgetQuery` dataclass + `parse_widget_query(dict)` |
| `shared_widget_query` update | `SharedWidgetQuery` dataclass + `parse_shared_widget_query(dict)` |
| TON wallet `type: data/sent_transaction/sign_data` | `WalletCard` / `WalletSentTransaction` / `WalletSignDataResult` |
| wallet transaction answer shape | `build_wallet_transaction_answer(valid_until, messages)` |
| `InputWidgetMessageContent` | `input_widget_message_content(html, ...)` |
| `InputSharedWidgetMessageContent` | `input_shared_widget_message_content(widget_id)` |
| generic update handling | `extract_widget_query(update)` (duck-types dict or object) |

Validated against the guide's stated limits:

- Widget HTML ≤ 4096 bytes compressed with zlib level 9
  (`widget_html_compressed_size`/`validate_widget_html`) — checked
  **before** any network call.
- `answerWidgetQuery` `data` ≤ 1024 bytes (UTF-8; see §4), optional
  15-second staleness check via `received_at`.
- `editSharedWidgetData` `cache_time` ∈ [5, 3600] seconds.
- Wallet transaction answers: 1–255 messages, each `amount` validated and
  normalised to a decimal nanoton string.
- `WidgetQuery`/`edit_message_widget_data` addressing: exactly one of
  (`chat`+`message_id`) or `inline_message_id` — enforced both when
  parsing an incoming query and when building an edit call.

### Why Bot HTTP API, not MTProto

richgram's existing rich-message support only works because Kurigram's
*MTProto* layer added native support for it (`InputRichMessage`,
`Client.send_rich_message` — that's what `RICH_AVAILABLE` detects). No
known Pyrogram/Kurigram release has MTProto-level widget support — the
feature was announced yesterday. So every widget function here talks
directly to the plain Bot HTTP API (`https://api.telegram.org/bot<token>/...`),
the same pattern `rich_ui._send_blocks_via_http` already uses for typed
blocks. This works the moment Telegram enables widgets for your bot,
independent of your Pyrogram/Kurigram build. A `WIDGET_NATIVE_AVAILABLE`
flag (mirroring `RICH_AVAILABLE`) is still checked first in every
function, so a future Kurigram release adding `Client.send_widget` etc.
is picked up automatically without an API change on richgram's side.

### Receiving queries

No library is known to parse `widget_query`/`shared_widget_query`
updates into Python objects yet, so there's no `@client.on_widget_query()`
decorator here — that would be fabricating support that doesn't exist.
Instead, `parse_widget_query`/`parse_shared_widget_query`/
`extract_widget_query` turn the **raw Bot-API-JSON dict** Telegram sends
(from a webhook, your own `getUpdates` poll, or, eventually, whatever a
library hands you) into the typed dataclasses above. The README shows
the intended usage and says plainly that a Kurigram-only bot will not
receive these updates at all until the library adds support.

## 3. Tests

`tests/unit/test_widgets.py`, same offline style as the rest of the
suite (`tests/helpers.py`'s `FakeClient` pattern, no network): an
`httpx.AsyncClient` fake records every call and feeds back queued
responses, so every HTTP-shaped test asserts both the request payload
sent and the result/exception produced. Covers:

- HTML size validation (good/empty/oversize, exact zlib-9 byte count)
- all five send/edit/answer functions: success path, request shape,
  `WidgetAPIError` on `ok:false`, argument validation, missing-token
  `RuntimeError`, native-method preference + HTTP fallback on native
  failure
- `parse_widget_query`/`parse_shared_widget_query`: required fields,
  addressing-form exclusivity, both chat and inline forms, all three
  wallet payload variants
- `extract_widget_query`: wrapped update dict, bare `widget_query`/
  `shared_widget_query` dict, object with `.widget_query` attribute,
  unrelated update → `None`
- `build_wallet_transaction_answer`: message-count bounds, amount
  normalisation/validation, missing fields
- inline-content builders

```
$ pytest -m "unit or guard"
299 passed, 1 deselected in 0.64s   (the integration test needs a real BOT_TOKEN)

$ pytest
299 passed, 1 skipped in 0.55s
```

Run against the **real** `kurigram` package (already present in this
environment, not the offline stub), plus `httpx`, `telethon>=1.45`,
`pytest`, `pytest-asyncio` — installed via `pip install -e ".[test,http]"`.
The pre-existing repository guard `test_no_comments_in_python_files`
(no `#` comments anywhere in the codebase) was kept satisfied in the new
files too.

## 4. Known gaps / honesty notes (per your requirement #1 and #6)

- **No fabricated parameters.** Every field/method name and every limit
  enforced here traces to a specific statement on
  `core.telegram.org/bots/widgets` (quoted in `richgram/widgets.py`'s
  module docstring). Where the guide didn't give a full required/optional
  table — it's a guide page, not the per-method reference table other
  Bot API methods get — this module validates what *is* stated and
  passes the rest through as given, rather than guessing types it wasn't
  shown.
- **`answerWidgetQuery` data is treated as UTF-8 text, not arbitrary
  bytes.** Bot API JSON has no raw-byte field type (same situation as
  `callback_data` elsewhere in the API), so `bytes` input is accepted
  only if it decodes as valid UTF-8; anything else raises `ValueError`
  telling the caller to encode it themselves (e.g. base64) rather than
  silently corrupting binary data.
- **Production vs. test server**: not special-cased. An `api_base=...`
  parameter is exposed on every function so a caller can point at
  Telegram's test-server namespace, but this module has no way to detect
  which server a token belongs to, and the guide page says nothing about
  the test server's limits possibly differing — so none of the validated
  limits (4096-byte HTML, 1024-byte answer data, etc.) are relaxed for
  it. Verify directly against the test server before relying on it there.
- **Nothing was run against a live bot token.** Per your instruction, no
  real credentials were used and nothing was pushed anywhere. The test
  suite validates request shape and local logic against the documented
  spec; it cannot validate that Telegram's actual server accepts exactly
  this payload shape. Recommended next step: a `tests/integrations` smoke
  test (the existing suite already has the scaffolding —
  `tests/integrations/test_live.py` — for `API_ID`/`API_HASH`/
  `BOT_TOKEN`/`CHAT_ID`) run once against a real bot before shipping.
- **`MAX_WIDGET_QUERY_REQUEST_BYTES` (1–64 bytes)** describes a limit on
  the *widget's own* outgoing `TelegramWidget.request(data)` call (client
  JS side) — richgram (server side) never constructs that payload, so
  this constant is exported for documentation/fixture use only and isn't
  enforced by any function here.

## 5. Backward compatibility

- `richgram/rich_ui.py` and `richgram/telethon.py`: **unchanged**, byte
  for byte.
- `richgram/__init__.py`: one additive block (imports and re-exports
  `widgets`); every previously existing top-level name is still present
  and unchanged, confirmed by the existing
  `tests/guards/test_repository.py::test_every_exported_name_exists` and
  `test_all_has_no_duplicates` guards (which now also check the merged
  `richgram.__all__`, including the new names), both passing.
- Version bumped `0.7.1` → `0.8.0` (additive feature, per semver).
- `pyproject.toml`: description line updated to mention 10.4; no
  dependency changed for the base install (widgets needs the existing
  `http` extra, `httpx`, same extra `rich_send_blocks`'s dict-block path
  already needed).

## 6. Files changed/added

```
richgram/__init__.py       modified (import + re-export widgets)
richgram/widgets.py         new      (~780 lines)
tests/unit/test_widgets.py  new      (~475 lines)
README.md                   modified (new "Widgets (Bot API 10.4)" section,
                                       updated intro/exports/requirements)
pyproject.toml               modified (description line)
FINAL_REPORT.md              new      (this file)
```

`richgram/rich_ui.py`, `richgram/telethon.py`, `bot.py`, all pre-existing
tests: unchanged.

## 7. Checksum

See `SHA256SUMS.txt` alongside the delivered zip for the archive's
SHA-256.
