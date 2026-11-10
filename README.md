# richgram

Telegram Bot API 10.3 rich messages for Pyrogram, Pyrofork and Kurigram bots:
tables, details, lists, colored buttons, drafts and ephemeral messages, with an
automatic plain-text fallback when a rich message is rejected. The same
builders also work over MTProto via the optional Telethon transport
(`richgram.telethon`). `richgram.widgets` adds Bot API 10.4 HTML widgets
(`sendWidget` and friends) on top — see [Widgets](#widgets-bot-api-104)
below.

## Install

```bash
pip install richgram
```

For the Telethon transport:

```bash
pip install "richgram[telethon]"
```

Or straight from GitHub:

```bash
pip install git+https://github.com/Badmunda05/richgram.git
```

## How to import

Import only what you need (recommended):

```python
from richgram import rich_send, rich_reply, rich_edit
from richgram import rich_heading, rich_note, rich_table, rich_kv_table
from richgram import rich_button, rich_button_row
```

Or import the whole package and use the `richgram.` prefix:

```python
import richgram

text = richgram.rich_heading("Hello", level=3)
await richgram.rich_send(client, chat_id, text)
```

Or import from the submodule directly:

```python
from richgram.rich_ui import rich_send, rich_button
```

Check the version and whether your build supports rich messages:

```python
import richgram

print(richgram.__version__)
print(richgram.RICH_AVAILABLE)
```

## Quick example

```python
from richgram import rich_send, rich_heading, rich_kv_table, rich_esc

text = (
    rich_heading("Now Playing", level=3)
    + rich_kv_table([
        ("Title", rich_esc("Song name")),
        ("Duration", "3:27"),
    ])
)

await rich_send(client, chat_id, text)
```

## Buttons

Buttons are part of the message HTML, so append them to the content
(there is no `reply_markup`):

```python
from richgram import rich_button, rich_button_row, rich_send

buttons = (
    rich_button_row(
        rich_button("Support", url="https://t.me/BadmundaXd", style="primary"),
        rich_button("Pause", callback_data="pause", style="success"),
    )
    + rich_button_row(rich_button("Close", callback_data="close", style="danger"))
)

await rich_send(client, chat_id, text + buttons)
```

- `style`: `primary` (blue), `success` (green), `danger` (red), `link`, or leave it out for grey.
- URL button: `type="url"` with `url="..."`.
- Callback button: `type="callback_data"` with `data="..."`.
- Copy button: `type="copy_text"` with `text="..."` — one tap copies the
  value to the clipboard. The text must be 1–256 characters, and a copy
  button takes no `url` or `callback_data`:

```python
rich_button("Copy ID", copy_text="5368324170671202286", style="primary")
```

  When a message falls back to plain text, a copy button becomes its bold
  label — the value itself is not shown.
- `rich_button_row(..., align="center")` aligns the row (`left`, `center`, `right`).

Random colours like an inline keyboard:

```python
import random

style = random.choice(["primary", "success", "danger"])
rich_button("Shuffle", callback_data="shuffle", style=style)
```

## Page indexation

The bottom line of a paginated message is an italic footer:

```python
from richgram import rich_page_index

rich_page_index(2, 5, total=42)              # Page 2 of 5 • total 42
rich_page_index(2, 5)                        # Page 2 of 5
rich_page_index(2, 5, label="Settings")     # Settings • Page 2 of 5
```

Page counts are 1-based, `pages` must cover `page`, and `total` must not
be negative. In plain-text fallback the line survives as `Page 2 of 5 •
total 42`.

## Premium (custom) emoji

```python
from richgram import rich_emoji, rich_send

await rich_send(client, chat_id, "Nice " + rich_emoji("5368324170671202286", "🔥") + " work!")
```

`rich_emoji(document_id, alt)` emits the Bot API form
`<tg-emoji emoji-id="...">🔥</tg-emoji>`. The id is the custom-emoji
sticker's **document id** — not a file_id, pack name, or `t.me/addemoji`
link, and it cannot be guessed. Get one from a message that already
contains the emoji (its `custom_emoji` entity), from a sticker set
(`Sticker.custom_emoji_id`), or verify one you have with:

```python
from richgram import fetch_custom_emoji

sticker = await fetch_custom_emoji(client, "5368324170671202286")
print(sticker.emoji)  # the fallback glyph to use as alt
```

`alt` is the plain emoji shown where the custom emoji cannot be
displayed (notifications, forwards by non-premium users, and richgram's
plain-text fallback), so it is required. A bot may send custom emoji if
its owner has Telegram Premium (direct messages to private, group and
supergroup chats) or if the bot purchased additional usernames on
Fragment (also channels). If the bot is not eligible, Telegram rejects
the message and richgram falls back to the alt text.

Register emoji once and use them by name, including `:shortcode:`
expansion in any text:

```python
from richgram import (
    add_html_hook, expand_emoji_shortcodes,
    register_custom_emoji, rich_emoji_named,
)

register_custom_emoji("fire", "5368324170671202286", "🔥")
add_html_hook(expand_emoji_shortcodes)

await rich_send(client, chat_id, "Nice :fire: work!")  # :fire: expands on send
rich_emoji_named("fire")  # the same markup, directly
```

Only registered names expand; unknown shortcodes and times like `12:30`
are left alone, and shortcodes inside `<pre>`/`<code>` are never
expanded. `register_custom_emojis({...})` registers many at once,
`custom_emoji_names()` lists them, `clear_custom_emojis()` clears them.

MarkdownV2 form, and the typed block form for `rich_send_blocks`:

```python
from richgram import rich_emoji_markdown, rich_text_custom_emoji

rich_emoji_markdown("5368324170671202286", "🔥")  # ![🔥](tg://emoji?id=...)
rich_text_custom_emoji("5368324170671202286", "🔥")  # RichTextCustomEmoji
```

The older Pyrogram form `<emoji id="...">🔥</emoji>` still works anywhere
in richgram input: it is normalised to `<tg-emoji emoji-id="...">` before
sending, since the rich path sends HTML raw to Telegram.

## Multiple collapsibles

One section is `rich_details(summary, body, open=False)`. For several
sections in one message, build them as a group:

```python
from richgram import rich_details_group

text = rich_details_group([
    ("Install", "pip install richgram"),
    ("Usage", "See the examples below.", True),  # open by default
    {"summary": "Source", "body": "Clone the repo and read rich_ui.py"},
])
```

`open_first=True` opens only the first section, `open_all=True` opens
every section, and a per-section `open` wins over both. Sections open and
close independently: Telegram has no accordion mode.

Sections nest, too — pass a `rich_details(...)` as a body, or build a
tree with `rich_details_nested`:

```python
from richgram import rich_details_nested

text = rich_details_nested("Guide", "Start here.", children=[
    ("Install", "pip install richgram"),
    {"summary": "Advanced", "body": "", "children": [
        ("Source", "Clone the repo and read rich_ui.py"),
    ]},
])
```

Telegram allows up to 16 levels of nested formatting and blocks (and up
to 500 blocks in a message, nested details included), so nesting deeper
than 16 raises `ValueError` instead of failing at send time.

Typed blocks for `rich_send_blocks` (nest one details block inside
another the same way):

```python
from richgram import rich_block_details, rich_block_paragraph

block = rich_block_details("Guide", [
    rich_block_paragraph("Start here."),
    rich_block_details("Advanced", [rich_block_paragraph("Deep dive.")]),
], open=True)
```

When a rich message is rejected and richgram falls back to plain text,
collapsibles become an indented outline (`▸` per section, deeper sections
indented), so the structure survives instead of collapsing flat.

## Todo lists

A checklist renders as native checkboxes — not emoji bullets:

```python
from richgram import rich_todo_list

text = rich_todo_list([
    ("Buy milk", False),
    ("Book tickets", True),
    "Call mom",  # a plain string is an unchecked item
    {"text": "Ship it", "done": True},
])
```

That is Rich HTML (`<li><input type="checkbox" checked>...`). The same
list as Rich Markdown, for `rich_send(..., markdown=True)`:

```python
from richgram import rich_todo_list_markdown

rich_todo_list_markdown([("Buy milk", False), ("Book tickets", True)])
# "- [ ] Buy milk\n- [x] Book tickets"
```

Or as typed blocks, for `rich_send_blocks` (Kurigram) and
`telethon_rich_send_blocks` (Telethon) — both carry the checkbox as a real
field (`has_checkbox` / `is_checked`, `checkbox` / `checked`):

```python
from richgram import rich_block_todo_list
from richgram.telethon import telethon_block_todo_list

rich_block_todo_list([("Buy milk", False), ("Book tickets", True)])
telethon_block_todo_list([("Buy milk", False), ("Book tickets", True)])
```

The boxes show the state you send; they are not tappable toggles. To flip
an item, re-send or edit the message with the new state. When a message
falls back to plain text, todo items render as `[ ] Buy milk` / `[x] Book
tickets`, so the state survives there too.

## Content blocks

```python
from richgram import (
    rich_heading, rich_note, rich_code, rich_pre, rich_list, rich_hr,
    rich_footer, rich_pull_quote, rich_math, rich_anchor, rich_thinking,
    rich_table, rich_kv_table, rich_details, rich_img, rich_esc,
)

rich_list(["one", "two"])
rich_list(["first", "second"], ordered=True)
rich_pre("print('hi')", language="python")
rich_table(["A"], [None, "single"])  # None rows render empty, string rows single-cell
rich_math("x^2 + y^2 = z^2")
rich_details("More", "hidden text", open=True)
```

## Code, inside and out

`rich_pre` escapes everything, so a code block is always literal text.
To nest inline formatting inside a code block — bold a keyword, mark a
value as inline code — use `rich_pre_rich`, whose body is HTML used
as-is (escape user text with `rich_esc` first):

```python
from richgram import rich_pre_rich

rich_pre_rich("<b>pip</b> install <code>richgram</code>", language="bash")
```

The language travels in the `<code class="language-...">` wrapper — the
form Telegram's parser reads. Any language string passes through; the
client highlights the languages it knows. A fenced Markdown block is
literal, so this nesting exists only in the HTML and typed-block forms.

As typed blocks, for `rich_send_blocks` (Kurigram) and
`telethon_rich_send_blocks` (Telethon), with the same segment model —
plain strings or `(kind, text)` pairs with kind `plain`/`bold`/`italic`/
`code`, or `RichText` objects from `rich_text_bold` / `rich_text_italic` /
`rich_text_code`:

```python
from richgram import rich_block_preformatted
from richgram.telethon import telethon_block_preformatted

rich_block_preformatted([
    ("bold", "pip"), " install ", ("code", "richgram"),
], language="bash")
telethon_block_preformatted([
    ("bold", "pip"), " install ", ("code", "richgram"),
], language="bash")
```

A pre-only message goes out over plain HTML (classic HTML already
renders `<pre>`), and joins the rich path when combined with rich-only
content such as a heading or a table.

## Map, collage, slideshow, audio, video

These blocks are sent as typed Kurigram blocks with `rich_send_blocks`:

```python
from pyrogram.types import InputRichBlockMap
from richgram import rich_send_blocks

await rich_send_blocks(client, chat_id, [InputRichBlockMap(...)])
```

## Sending and editing

```python
from richgram import rich_reply, rich_edit, rich_edit_inline, rich_answer

msg = await rich_reply(message, text)
await rich_edit(msg, text + buttons)
await rich_edit(callback_query, text + buttons)
await rich_edit_inline(client, inline_message_id, text)
await rich_answer(callback_query, text)
```

Extra options on `rich_send`, `rich_reply` and `rich_edit`:

```python
await rich_send(
    client, chat_id, text,
    business_connection_id="...",
    direct_messages_topic_id=5,
    message_thread_id=9,
    allow_paid_broadcast=True,
    suggested_post_parameters=params,
    disable_notification=True,
    protect_content=True,
    effect_id=123,
    is_rtl=True,
    skip_entity_detection=True,
)
```

Markdown instead of HTML:

```python
await rich_send(client, chat_id, "# Title\n\n**bold** text", markdown=True)
```

## Telethon (MTProto)

Telethon has no `send_rich_message`, but the same rich payload travels
over MTProto as a native request. `richgram.telethon` builds it for you —
the HTML builders are transport-independent, so the same text works on
both transports:

```python
from telethon import TelegramClient
from richgram import rich_heading, rich_details_group
from richgram.telethon import telethon_rich_send, telethon_rich_edit

client = TelegramClient("session", api_id, api_hash)

text = rich_heading("Now Playing", level=3) + rich_details_group([
    ("Track", "Song name"),
    ("Lyrics", "La la la"),
])

msg = await telethon_rich_send(client, chat_id, text)
await telethon_rich_edit(msg, text + " (updated)")
```

How it works: the adapter sends a raw `messages.SendMessageRequest` /
`messages.EditMessageRequest` with `rich_message` set to an
`InputRichMessageHTML` / `InputRichMessageMarkdown` (the same mechanism
Hermes uses). The TL schema still requires the ordinary `message` field,
so it is filled with the same rich source text. Telethon resolves the
peer and generates `random_id` itself when the request is invoked.

Like `rich_send`, a rich request Telegram rejects falls back to an
ordinary Telethon `send_message` with the plain fallback text — and
Telethon's HTML parser understands `<tg-emoji>`, so premium emoji survive
the plain path too. A raw send returns `Updates`, so the adapter resolves
the real `Message` from it before returning — `msg.id` works on the
return value of every send/edit call. A `FloodWaitError` is re-raised
from both paths, never swallowed into `None` and never fallen back from,
so the caller can sleep and retry. The builders for replies and blocks mirror the
Pyrogram side:

```python
from richgram.telethon import (
    telethon_rich_reply, telethon_rich_send_blocks,
    telethon_block_details, telethon_block_paragraph,
)

await telethon_rich_reply(message, text)
await telethon_rich_send_blocks(client, chat_id, [
    telethon_block_details("Guide", [telethon_block_paragraph("Start here.")]),
])
```

Blocks are Telethon `PageBlock` objects, not Pyrogram `InputRichBlock`
objects: `PageBlockDetails(blocks, title, open)` takes its arguments in
the opposite order to Pyrogram's `InputRichBlockDetails(summary, blocks)`.
`telethon_send_request` / `telethon_edit_request` return the raw requests
directly if you want to invoke them yourself, and `TELETHON_RICH_AVAILABLE`
reports whether the installed Telethon build has the rich-message types
(telethon>=1.45 is known to work).

## Ephemeral messages

```python
from richgram import rich_reply, ephemeral_edit, ephemeral_delete

sent = await rich_reply(message, text, ephemeral=True)
await ephemeral_edit(sent, new_text)
await ephemeral_delete(sent)
```

## Streaming drafts

```python
from richgram import RichDraft, rich_heading

async with RichDraft(client, chat_id, can_stop=True) as draft:
    await draft.update(rich_heading("Searching..."))
    await draft.finish(final_text)
```

## Fallback and debugging

If Telegram rejects a rich message, richgram sends a readable plain-text version
instead (buttons become links or bold text). To see why a rich message failed:

```python
import logging

logging.getLogger("richgram").setLevel(logging.DEBUG)
```

Transform HTML before it is sent (for example expanding emoji shortcodes):

```python
from richgram import add_html_hook, expand_emoji_shortcodes, register_custom_emoji

register_custom_emoji("fire", "5368324170671202286", "🔥")
add_html_hook(expand_emoji_shortcodes)  # turns :fire: into a premium emoji
```

Plain-text helpers: `rich_to_plain(html)` and `rich_caption(html)`.

## Everything you can import

`RICH_AVAILABLE`, `rich_esc`, `sanitize_display_name`, `rich_heading`,
`rich_note`, `rich_table`, `rich_kv_table`, `rich_details`,
`rich_details_group`, `rich_details_nested`, `rich_block_details`,
`rich_block_paragraph`, `rich_code`,
`rich_pre`, `rich_pre_rich`, `rich_block_preformatted`, `rich_text_bold`,
`rich_text_italic`, `rich_text_code`, `rich_list`, `rich_todo_list`, `rich_todo_list_markdown`,
`rich_block_todo_list`, `rich_hr`, `rich_footer`, `rich_page_index`,
`rich_pull_quote`,
`rich_math`, `rich_anchor`, `rich_thinking`, `rich_img`, `rich_emoji`,
`rich_emoji_markdown`, `rich_text_custom_emoji`, `register_custom_emoji`,
`register_custom_emojis`, `clear_custom_emojis`, `custom_emoji_names`,
`rich_emoji_named`, `expand_emoji_shortcodes`, `fetch_custom_emoji`,
`rich_button`, `rich_button_row`, `rich_to_plain`, `rich_caption`,
`add_html_hook`, `clear_html_hooks`, `rich_send`, `rich_send_blocks`,
`rich_reply`, `rich_edit`, `rich_edit_inline`, `rich_answer`,
`ephemeral_edit`, `ephemeral_delete`, `RichDraft`

Telethon transport (`from richgram.telethon import ...`):
`TELETHON_RICH_AVAILABLE`, `telethon_input_rich`, `telethon_send_request`,
`telethon_edit_request`, `telethon_block_paragraph`, `telethon_block_details`,
`telethon_block_todo_list`, `telethon_block_preformatted`, `telethon_rich_send`, `telethon_rich_send_blocks`, `telethon_rich_reply`,
`telethon_rich_edit`

Widgets (`from richgram import ...`, or `from richgram.widgets import ...`):
`WIDGET_NATIVE_AVAILABLE`, `MAX_WIDGET_HTML_COMPRESSED_BYTES`,
`MAX_WIDGET_QUERY_REQUEST_BYTES`, `MAX_WIDGET_ANSWER_DATA_BYTES`,
`MIN_WIDGET_CACHE_TIME`, `MAX_WIDGET_CACHE_TIME`, `MAX_WALLET_MESSAGES`,
`WidgetAPIError`, `WalletCard`, `WalletSentTransaction`,
`WalletSignDataResult`, `WidgetQuery`, `SharedWidgetQuery`,
`widget_html_compressed_size`, `validate_widget_html`,
`validate_nanoton_amount`, `parse_widget_query`,
`parse_shared_widget_query`, `extract_widget_query`,
`build_wallet_transaction_answer`, `send_widget`, `send_shared_widget`,
`edit_message_widget_data`, `edit_shared_widget_data`,
`answer_widget_query`, `input_widget_message_content`,
`input_shared_widget_message_content`

## Widgets (Bot API 10.4)

`richgram.widgets` adds Telegram's **widgets**: small, sandboxed HTML
blocks a bot draws inside a message (`core.telegram.org/bots/widgets`).
This is a separate feature from the rich messages above — it does not
need `RICH_AVAILABLE`/Kurigram's rich-message support, and nothing in
this section changes how `rich_send` and friends behave.

```python
from richgram import send_widget, answer_widget_query, parse_widget_query

msg = await send_widget(
    client, chat_id,
    "<!doctype html><html><body>Hello from a widget</body></html>",
    allow_queries=True,
)
```

Every function in this module talks to the plain Bot HTTP API directly
(`https://api.telegram.org/bot<token>/...`), the same escape hatch
`rich_send_blocks` already uses for typed blocks — it does not depend on
your Pyrogram/Kurigram build having native MTProto support for widgets
(no known release does yet). Pass `token=...` explicitly, or use a client
that already exposes `.bot_token` (Kurigram bot clients do). If a future
Kurigram release adds `Client.send_widget` and friends, this module
prefers them automatically (`WIDGET_NATIVE_AVAILABLE`) and only falls
back to the raw HTTP call on failure or absence.

```python
from richgram import send_shared_widget, edit_message_widget_data, edit_shared_widget_data

await send_shared_widget(client, chat_id, widget_id)
await edit_message_widget_data(client, chat_id=chat_id, message_id=msg["message_id"], public_data={"score": 10})
await edit_shared_widget_data(client, widget_id, public_data={"score": 11}, cache_time=30)
```

- `send_widget(client, chat_id, html, *, allow_queries=None, is_shared=None, width=None, height=None, ...)`
  — `html` is checked against the documented 4096-byte (zlib level 9
  compressed) limit before anything is sent
  (`widget_html_compressed_size(html)` to check it yourself).
- `send_shared_widget(client, chat_id, widget_id, ...)` re-sends an
  existing shared widget, the way a photo is re-sent by `file_id`.
- `edit_message_widget_data(client, *, chat_id=None, message_id=None, inline_message_id=None, chat_data=None, public_data=None)`
  — exactly one of (`chat_id` + `message_id`) or `inline_message_id`.
- `edit_shared_widget_data(client, widget_id, *, public_data=None, cache_time=None)`
  — `cache_time` is 5–3600 seconds.
- `answer_widget_query(client, widget_query_id, data=None, *, received_at=None)`
  — `data` is UTF-8 text up to 1024 bytes; pass `received_at=time.time()`
  (captured when the query arrived) to get an early `ValueError` instead
  of a late rejection if you're past Telegram's 15-second window.

All five raise `WidgetAPIError` (carrying `.error_code`/`.description`)
on an `ok: false` Bot API response, and `ValueError` on a bad argument —
unlike the rich-message senders above, they do not swallow failures into
`None`.

### Receiving `widget_query` / `shared_widget_query`

No known Pyrogram/Kurigram release parses these updates into Python
objects yet, so there is no `@client.on_widget_query()`-style handler
here. What richgram provides instead is a parser for the raw Bot-API-JSON
shape of the update — useful whether that JSON comes from a webhook, a
`getUpdates` poll you run yourself, or (once a library adds support) an
object a future Kurigram hands you:

```python
from richgram import extract_widget_query, answer_widget_query

query = extract_widget_query(update)  # update: a dict, or an object exposing .widget_query
if query is not None:
    await answer_widget_query(client, query.id, data="pong")
```

`extract_widget_query` accepts a whole update dict (`{"update_id": ..., "widget_query": {...}}`),
a bare `widget_query`/`shared_widget_query` dict, or an object exposing
`.widget_query`/`.shared_widget_query`, and returns a `WidgetQuery`, a
`SharedWidgetQuery`, or `None`. Use `parse_widget_query(data)` /
`parse_shared_widget_query(data)` directly if you already know which one
you have.

A `WidgetQuery` carries `id`, `from_user`, `chat_instance`, `widget_id`,
`data` (bytes), and either `chat`+`message_id` or `inline_message_id`.
Its `.wallet` field is a `WalletCard`, `WalletSentTransaction` or
`WalletSignDataResult` when the query is a TON Wallet response, parsed
from the `type` payload the guide describes. A `SharedWidgetQuery` (from
a forward of a shared widget) carries only `id`, `from_user`, `widget_id`
and `data`.

### TON Wallet transactions

```python
from richgram import build_wallet_transaction_answer

answer = build_wallet_transaction_answer(
    valid_until=int(time.time()) + 300,
    messages=[{"address": "EQ...", "amount": 1_000_000_000}],  # 1 TON, in nanotons
)
```

`build_wallet_transaction_answer` builds the TON Connect-shaped
`{valid_until, messages}` object the guide describes for answering a
wallet request; 1–255 messages, each `amount` normalised to a decimal
nanoton string (`validate_nanoton_amount`).

### Inline mode

`input_widget_message_content(html, ...)` and
`input_shared_widget_message_content(widget_id)` build the
`InputWidgetMessageContent` / `InputSharedWidgetMessageContent` dicts the
guide names for `answerInlineQuery`; richgram does not wrap
`answerInlineQuery` itself (it already exists on Pyrogram/Kurigram
clients), so pass these as one of the `results` there.

### What this module does **not** cover, and why

- As of this writing, `core.telegram.org/bots/api` (the full method/type
  reference) still tops out at **Bot API 10.3** and does not list
  `sendWidget`. Everything above is built against the separate, already
  published guide page at `core.telegram.org/bots/widgets`, which does
  document these methods, fields and limits — but that page is a guide,
  not the full parameter-table reference other methods get, so a few
  parameters' exact required/optional status was not spelled out there.
  This module validates every limit the guide page does pin down and
  passes everything else through unchanged; see the docstring at the top
  of `richgram/widgets.py` for the full list of what is, and isn't,
  confirmed.
- **Test server vs. production**: this module does not special-case
  Telegram's test-server token namespace (`.../bot<token>/test/...`).
  Pass a test-server token via `token=...`/`api_base=...` and it behaves
  the same way, but size/rate limits and feature availability there are
  not guaranteed to match production, and this module cannot tell which
  one it's talking to.
- Nothing here has been exercised against a live bot token or a real
  widget; the test suite (`tests/unit/test_widgets.py`) mocks the HTTP
  layer against the shapes the guide documents. Verify against a real bot
  before shipping.

## Demo bot

`bot.py` is a small demo bot (`/start` with shuffling button colours):

```bash
API_ID=123 API_HASH=abc BOT_TOKEN=123:xyz python bot.py
```

## Tests

```bash
pip install -e ".[test]"
pytest -m "unit or guard"
```

The unit tests use fake clients and messages, so they need no Telegram
connection. `tests/integrations` sends a real message when `API_ID`,
`API_HASH`, `BOT_TOKEN` and `CHAT_ID` are set.

## Used by

- [ShizuMusic](https://github.com/Badmunda05/ShizuMusic) Telegram music bot

## Requirements

- Python 3.10+
- A **Pyrogram / Pyrofork / Kurigram** build that has Bot API 10.3 rich message
  support (`InputRichMessage` and `Client.send_rich_message`).
  `RICH_AVAILABLE` is `True` when your build has it.
- For the Telethon transport: **Telethon >= 1.45** (`pip install "richgram[telethon]"`).
  `TELETHON_RICH_AVAILABLE` is `True` when the installed Telethon build has
  the rich-message types.
- For widgets: **httpx** (`pip install "richgram[http]"`), used for the
  direct Bot HTTP API calls `richgram.widgets` makes. A bot token, either
  passed as `token=...` or read from `client.bot_token`.

## Credits

- **[Kurigram](https://github.com/kurigram-org/kurigram)** for Bot API 10.3 rich message
  support in the Pyrogram ecosystem. Full credit to the Kurigram developers.
- richgram by [BadmundaXd](https://t.me/BadmundaXd).
