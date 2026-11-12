# nextgram

Telegram Bot API 10.3 rich messages — tables, details, lists, colored
buttons, drafts and ephemeral messages, with an automatic plain-text
fallback when a rich message is rejected — plus Bot API 10.4 HTML widgets
(`sendWidget` and friends, see [Widgets](#widgets-bot-api-104) below), for
six frameworks:

| Framework | Module | Rich messages | Widgets |
|---|---|---|---|
| Pyrogram / Pyrofork / Kurigram | `nextgram.rich_ui` (also the top-level `nextgram.*` names) | native (`InputRichMessage`) when the installed build supports it, HTML fallback otherwise | yes |
| Telethon | `nextgram.telethon` | native MTProto `rich_message` when the installed build supports it, HTML fallback otherwise | yes |
| aiogram | `nextgram.aiogram_rich` | `sendRichMessage` over the plain Bot HTTP API, HTML fallback otherwise | yes |
| python-telegram-bot | `nextgram.ptb_rich` | `sendRichMessage` over the plain Bot HTTP API, HTML fallback otherwise | yes |

Pyrogram, Pyrofork and Kurigram are one family — three distributions of
the exact same `pyrogram` package name — so one implementation already
covers all three; there is nothing framework-specific left to add for
them. `nextgram.widgets` is framework-agnostic by construction (it only
ever needs a bot token) and already works unmodified from every framework
above.

Installing `nextgram` on its own needs none of Pyrogram, Pyrofork,
Kurigram, Telethon, aiogram or python-telegram-bot — only `httpx`, for the
HTTP calls `nextgram.widgets` (and the aiogram/python-telegram-bot rich
senders) make. Each framework's own module is only imported when you
import it, so a bot using just one framework never needs the others
installed.

## Install

```bash
pip install nextgram
```

With the framework you actually use:

```bash
pip install "nextgram[pyrogram]"      # Pyrogram, Pyrofork or Kurigram (one package: kurigram)
pip install "nextgram[telethon]"
pip install "nextgram[aiogram]"
pip install "nextgram[ptb]"           # python-telegram-bot
pip install "nextgram[all]"           # every framework, for trying things out
```

Or straight from GitHub:

```bash
pip install git+https://github.com/Badmunda05/nextgram.git
```

## How to import

Import only what you need (recommended):

```python
from nextgram import rich_send, rich_reply, rich_edit
from nextgram import rich_heading, rich_note, rich_table, rich_kv_table
from nextgram import rich_button, rich_button_row
```

Or import the whole package and use the `nextgram.` prefix:

```python
import nextgram

text = nextgram.rich_heading("Hello", level=3)
await nextgram.rich_send(client, chat_id, text)
```

Or import from the submodule directly:

```python
from nextgram.rich_ui import rich_send, rich_button
```

Check the version and whether your build supports rich messages:

```python
import nextgram

print(nextgram.__version__)
print(nextgram.RICH_AVAILABLE)
```

## Quick example

```python
from nextgram import rich_send, rich_heading, rich_kv_table, rich_esc

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
from nextgram import rich_button, rich_button_row, rich_send

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
from nextgram import rich_page_index

rich_page_index(2, 5, total=42)              # Page 2 of 5 • total 42
rich_page_index(2, 5)                        # Page 2 of 5
rich_page_index(2, 5, label="Settings")     # Settings • Page 2 of 5
```

Page counts are 1-based, `pages` must cover `page`, and `total` must not
be negative. In plain-text fallback the line survives as `Page 2 of 5 •
total 42`.

## Premium (custom) emoji

```python
from nextgram import rich_emoji, rich_send

await rich_send(client, chat_id, "Nice " + rich_emoji("5368324170671202286", "🔥") + " work!")
```

`rich_emoji(document_id, alt)` emits the Bot API form
`<tg-emoji emoji-id="...">🔥</tg-emoji>`. The id is the custom-emoji
sticker's **document id** — not a file_id, pack name, or `t.me/addemoji`
link, and it cannot be guessed. Get one from a message that already
contains the emoji (its `custom_emoji` entity), from a sticker set
(`Sticker.custom_emoji_id`), or verify one you have with:

```python
from nextgram import fetch_custom_emoji

sticker = await fetch_custom_emoji(client, "5368324170671202286")
print(sticker.emoji)  # the fallback glyph to use as alt
```

`alt` is the plain emoji shown where the custom emoji cannot be
displayed (notifications, forwards by non-premium users, and nextgram's
plain-text fallback), so it is required. A bot may send custom emoji if
its owner has Telegram Premium (direct messages to private, group and
supergroup chats) or if the bot purchased additional usernames on
Fragment (also channels). If the bot is not eligible, Telegram rejects
the message and nextgram falls back to the alt text.

Register emoji once and use them by name, including `:shortcode:`
expansion in any text:

```python
from nextgram import (
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
from nextgram import rich_emoji_markdown, rich_text_custom_emoji

rich_emoji_markdown("5368324170671202286", "🔥")  # ![🔥](tg://emoji?id=...)
rich_text_custom_emoji("5368324170671202286", "🔥")  # RichTextCustomEmoji
```

The older Pyrogram form `<emoji id="...">🔥</emoji>` still works anywhere
in nextgram input: it is normalised to `<tg-emoji emoji-id="...">` before
sending, since the rich path sends HTML raw to Telegram.

## Multiple collapsibles

One section is `rich_details(summary, body, open=False)`. For several
sections in one message, build them as a group:

```python
from nextgram import rich_details_group

text = rich_details_group([
    ("Install", "pip install nextgram"),
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
from nextgram import rich_details_nested

text = rich_details_nested("Guide", "Start here.", children=[
    ("Install", "pip install nextgram"),
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
from nextgram import rich_block_details, rich_block_paragraph

block = rich_block_details("Guide", [
    rich_block_paragraph("Start here."),
    rich_block_details("Advanced", [rich_block_paragraph("Deep dive.")]),
], open=True)
```

When a rich message is rejected and nextgram falls back to plain text,
collapsibles become an indented outline (`▸` per section, deeper sections
indented), so the structure survives instead of collapsing flat.

## Todo lists

A checklist renders as native checkboxes — not emoji bullets:

```python
from nextgram import rich_todo_list

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
from nextgram import rich_todo_list_markdown

rich_todo_list_markdown([("Buy milk", False), ("Book tickets", True)])
# "- [ ] Buy milk\n- [x] Book tickets"
```

Or as typed blocks, for `rich_send_blocks` (Kurigram) and
`telethon_rich_send_blocks` (Telethon) — both carry the checkbox as a real
field (`has_checkbox` / `is_checked`, `checkbox` / `checked`):

```python
from nextgram import rich_block_todo_list
from nextgram.telethon import telethon_block_todo_list

rich_block_todo_list([("Buy milk", False), ("Book tickets", True)])
telethon_block_todo_list([("Buy milk", False), ("Book tickets", True)])
```

The boxes show the state you send; they are not tappable toggles. To flip
an item, re-send or edit the message with the new state. When a message
falls back to plain text, todo items render as `[ ] Buy milk` / `[x] Book
tickets`, so the state survives there too.

## Content blocks

```python
from nextgram import (
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
from nextgram import rich_pre_rich

rich_pre_rich("<b>pip</b> install <code>nextgram</code>", language="bash")
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
from nextgram import rich_block_preformatted
from nextgram.telethon import telethon_block_preformatted

rich_block_preformatted([
    ("bold", "pip"), " install ", ("code", "nextgram"),
], language="bash")
telethon_block_preformatted([
    ("bold", "pip"), " install ", ("code", "nextgram"),
], language="bash")
```

A pre-only message goes out over plain HTML (classic HTML already
renders `<pre>`), and joins the rich path when combined with rich-only
content such as a heading or a table.

## Map, collage, slideshow, audio, video

These blocks are sent as typed Kurigram blocks with `rich_send_blocks`:

```python
from pyrogram.types import InputRichBlockMap
from nextgram import rich_send_blocks

await rich_send_blocks(client, chat_id, [InputRichBlockMap(...)])
```

## Sending and editing

```python
from nextgram import rich_reply, rich_edit, rich_edit_inline, rich_answer

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
over MTProto as a native request. `nextgram.telethon` builds it for you —
the HTML builders are transport-independent, so the same text works on
both transports:

```python
from telethon import TelegramClient
from nextgram import rich_heading, rich_details_group
from nextgram.telethon import telethon_rich_send, telethon_rich_edit

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
`InputRichMessageHTML` / `InputRichMessageMarkdown`. The TL schema still
requires the ordinary `message` field, so it is filled with the same rich
source text. Telethon resolves the peer and generates `random_id` itself
when the request is invoked.

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
from nextgram.telethon import (
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

## aiogram

aiogram has no MTProto layer and no native rich-message method, so
`nextgram.aiogram_rich` goes straight to the plain Bot HTTP API's
`sendRichMessage` endpoint — the same endpoint the Pyrogram side falls
back to over HTTP for typed blocks — and falls back further to an
ordinary `sendMessage` with the plain-fallback text if that is rejected:

```python
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from nextgram import rich_heading, rich_details_group
from nextgram.aiogram_rich import aiogram_rich_send, aiogram_rich_reply

bot = Bot(token=TOKEN)
dp = Dispatcher()

text = rich_heading("Now Playing", level=3) + rich_details_group([
    ("Track", "Song name"),
    ("Lyrics", "La la la"),
])

@dp.message(Command("np"))
async def now_playing(message):
    await aiogram_rich_reply(message, text)
```

`aiogram_rich_send(bot, chat_id, html_text, ...)` takes a `Bot` instance
directly, reading its token from `bot.token`. `aiogram_rich_reply(message,
html_text, ...)` reads both the bot and the chat off an aiogram `Message`
automatically (aiogram sets `message.bot` on every incoming message).
`aiogram_rich_edit(message, html_text, ...)` edits in place; pass
`chat_id=`/`message_id=` instead of `message` to edit one you don't have
the `Message` object for. A `reply_markup` can be an aiogram
`InlineKeyboardMarkup` or a plain dict — it's converted automatically.

These functions return the Bot API `result` dict (with `message_id`), not
an aiogram `Message` object — aiogram's own send methods are never called,
since the whole point is reaching `sendRichMessage`, which aiogram doesn't
know about.

## python-telegram-bot

Same situation as aiogram: no MTProto, no native rich-message method, so
`nextgram.ptb_rich` also goes through the plain Bot HTTP API's
`sendRichMessage`, with the same fallback to `sendMessage`:

```python
from telegram.ext import Application, CommandHandler
from nextgram import rich_heading, rich_details_group
from nextgram.ptb_rich import ptb_rich_reply

text = rich_heading("Now Playing", level=3) + rich_details_group([
    ("Track", "Song name"),
    ("Lyrics", "La la la"),
])

async def now_playing(update, context):
    await ptb_rich_reply(update, text)

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("np", now_playing))
```

`ptb_rich_send(bot, chat_id, html_text, ...)` takes a `Bot` (or
`context.bot`) directly, reading its token from `bot.token`.
`ptb_rich_reply(message_or_update, html_text, ...)` accepts either a
`telegram.Message` or a `telegram.Update` (its `.effective_message` is
used), and reads the bot via `message.get_bot()`.
`ptb_rich_edit(message, html_text, ...)` edits in place; pass
`chat_id=`/`message_id=`/`bot=` instead of `message` to edit one you don't
have the `Message` object for. A `reply_markup` can be a
python-telegram-bot `InlineKeyboardMarkup` or a plain dict.

Like aiogram, these functions return the Bot API `result` dict, not a
`telegram.Message`.

## How the HTTP-based `sendRichMessage` path works, and what's unconfirmed

`nextgram.http_rich` is what `aiogram_rich` and `ptb_rich` both build on.
It POSTs to `https://api.telegram.org/bot<token>/sendRichMessage` with
`{"chat_id": ..., "rich_message": {"html": ...}}` — this is a real,
already-used endpoint (`rich_ui._send_blocks_via_http` calls the same one
for typed blocks), not a guess specific to this module. Sending is
reasonably solid: a rejection is caught and the message goes out as plain
HTML instead.

Editing is the part that's genuinely unconfirmed: there is no documented
standalone HTTP method for editing a rich message, only Pyrogram's native,
MTProto-level `edit_message_text(..., rich_message=...)`. `edit_rich_html_via_http`
tries the same `rich_message` field on the plain HTTP `editMessageText`
call first — it may or may not be honoured by the server — and falls back
to a plain-HTML edit either way, so an edit never fails outright; it may
just silently land as a plain-text edit instead of a rich one. If you hit
this, the plain-text edit is still correct content, just not rich.

## Ephemeral messages

```python
from nextgram import rich_reply, ephemeral_edit, ephemeral_delete

sent = await rich_reply(message, text, ephemeral=True)
await ephemeral_edit(sent, new_text)
await ephemeral_delete(sent)
```

## Streaming drafts

```python
from nextgram import RichDraft, rich_heading

async with RichDraft(client, chat_id, can_stop=True) as draft:
    await draft.update(rich_heading("Searching..."))
    await draft.finish(final_text)
```

## Fallback and debugging

If Telegram rejects a rich message, nextgram sends a readable plain-text version
instead (buttons become links or bold text). To see why a rich message failed:

```python
import logging

logging.getLogger("nextgram").setLevel(logging.DEBUG)
```

Transform HTML before it is sent (for example expanding emoji shortcodes):

```python
from nextgram import add_html_hook, expand_emoji_shortcodes, register_custom_emoji

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

Telethon transport (`from nextgram.telethon import ...`):
`TELETHON_RICH_AVAILABLE`, `telethon_input_rich`, `telethon_send_request`,
`telethon_edit_request`, `telethon_block_paragraph`, `telethon_block_details`,
`telethon_block_todo_list`, `telethon_block_preformatted`, `telethon_rich_send`, `telethon_rich_send_blocks`, `telethon_rich_reply`,
`telethon_rich_edit`

aiogram transport (`from nextgram.aiogram_rich import ...`):
`aiogram_bot_token`, `aiogram_rich_send`, `aiogram_rich_reply`,
`aiogram_rich_edit`

python-telegram-bot transport (`from nextgram.ptb_rich import ...`):
`ptb_bot_token`, `ptb_rich_send`, `ptb_rich_reply`, `ptb_rich_edit`

Shared HTTP layer behind both of the above (`from nextgram.http_rich
import ...`): `send_rich_html_via_http`, `edit_rich_html_via_http`,
`coerce_markup_to_dict`

Widgets (`from nextgram import ...`, or `from nextgram.widgets import ...`)
— the same names work from every framework above, including Telethon,
aiogram and python-telegram-bot, since this module never touches a
framework's client type directly, only a bot token:
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

`nextgram.widgets` adds Telegram's **widgets**: small, sandboxed HTML
blocks a bot draws inside a message (`core.telegram.org/bots/widgets`).
This is a separate feature from the rich messages above — it does not
need `RICH_AVAILABLE`/Kurigram's rich-message support, and nothing in
this section changes how `rich_send` and friends behave.

```python
from nextgram import send_widget, answer_widget_query, parse_widget_query

msg = await send_widget(
    client, chat_id,
    "<!doctype html><html><body>Hello from a widget</body></html>",
    allow_queries=True,
)
```

Every function in this module talks to the plain Bot HTTP API directly
(`https://api.telegram.org/bot<token>/...`), the same escape hatch
`rich_send_blocks` already uses for typed blocks — it does not depend on
any framework's client having native MTProto/HTTP support for widgets (no
known release of any of the six frameworks does yet). Pass `token=...`
explicitly, or pass a client that already exposes the token itself:
`.bot_token` (Pyrogram, Pyrofork, Kurigram) or `.token` (aiogram,
python-telegram-bot) are both read automatically. Telethon's
`TelegramClient` doesn't keep the bot token it logged in with, so pass
`token=...` for it. If a future release of any framework adds native
widget support, this module prefers it automatically
(`WIDGET_NATIVE_AVAILABLE`) and only falls back to the raw HTTP call on
failure or absence.

```python
from nextgram import send_shared_widget, edit_message_widget_data, edit_shared_widget_data

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
here. What nextgram provides instead is a parser for the raw Bot-API-JSON
shape of the update — useful whether that JSON comes from a webhook, a
`getUpdates` poll you run yourself, or (once a library adds support) an
object a future Kurigram hands you:

```python
from nextgram import extract_widget_query, answer_widget_query

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
from nextgram import build_wallet_transaction_answer

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
guide names for `answerInlineQuery`; nextgram does not wrap
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
  of `nextgram/widgets.py` for the full list of what is, and isn't,
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
- **httpx**, always required (a plain `pip install nextgram` pulls it in) —
  it's what `nextgram.widgets` and the aiogram/python-telegram-bot rich
  senders use for their direct Bot HTTP API calls.
- Only the framework(s) you actually use — none of the other five are
  required to install or import `nextgram`:
  - **Pyrogram / Pyrofork / Kurigram** (`pip install "nextgram[pyrogram]"`,
    or the matching fork directly — all three install as the same
    `pyrogram` package name). Native rich-message support
    (`InputRichMessage`/`Client.send_rich_message`) is used automatically
    when the installed build has it; `RICH_AVAILABLE` says whether it
    does. No known build has it yet, so the HTML fallback is what actually
    runs today.
  - **Telethon >= 1.45** (`pip install "nextgram[telethon]"`).
    `TELETHON_RICH_AVAILABLE` says whether the installed build has the
    rich-message types.
  - **aiogram >= 3.0** (`pip install "nextgram[aiogram]"`).
  - **python-telegram-bot >= 21.0** (`pip install "nextgram[ptb]"`).
- A bot token for widgets and for the aiogram/python-telegram-bot rich
  senders — passed as `token=...`, or read automatically from a client's
  `.bot_token` (Pyrogram/Pyrofork/Kurigram) or `.token` (aiogram,
  python-telegram-bot) attribute. Telethon has neither, so pass
  `token=...` explicitly when using it with `nextgram.widgets`.

## Credits

- **[Kurigram](https://github.com/kurigram-org/kurigram)** for Bot API 10.3 rich message
  support in the Pyrogram ecosystem. Full credit to the Kurigram developers.
- nextgram by [BadmundaXd](https://t.me/BadmundaXd).
