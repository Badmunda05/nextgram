# NEXTGRAM

Telegram Bot API 10.3 rich messages and 10.4 HTML widgets for Pyrogram, Pyrofork, Kurigram, Telethon, aiogram and python-telegram-bot.

## Install

```bash
pip install nextgram
```

Requires Python 3.10+ and httpx. Install only the framework you use.

| Framework | Module | Optional extra |
|---|---|---|
| Pyrogram / Pyrofork / Kurigram | `nextgram.rich_ui` | `pyrogram` (Kurigram) |
| Telethon | `nextgram.telethon` | `telethon` |
| aiogram | `nextgram.aiogram_rich` | `aiogram` |
| python-telegram-bot | `nextgram.ptb_rich` | `ptb` |

## Quick start

```python
from nextgram import rich_send, rich_heading, rich_kv_table

text = rich_heading("Now Playing", level=3) + rich_kv_table([
    ("Title", "Song name"), ("Duration", "3:27")
])
await rich_send(client, chat_id, text)
```

Native rich messages require a compatible client build. Otherwise, senders fall back to plain HTML; embedded rich buttons may become text. HTTP rich edits are not verified live.

## Widgets

```python
from nextgram import send_widget

await send_widget(None, chat_id, "<h1>Hello</h1>", token=bot_token)
```

Widgets support shared data, queries, inline content and TON wallet payloads. Native query handlers are used when available; other clients can parse raw updates. Pass a bot token explicitly when the client does not expose one.

## Rich message API

- `RICH_AVAILABLE`, `rich_esc`, `sanitize_display_name`, `rich_heading`, `rich_note`
- `rich_table`, `rich_kv_table`, `rich_details`, `rich_details_group`, `rich_details_nested`
- `rich_block_details`, `rich_block_paragraph`, `rich_code`, `rich_pre`, `rich_pre_rich`
- `rich_block_preformatted`, `rich_text_bold`, `rich_text_italic`, `rich_text_code`, `rich_list`
- `rich_todo_list`, `rich_todo_list_markdown`, `rich_block_todo_list`, `rich_hr`, `rich_footer`
- `rich_page_index`, `rich_pull_quote`, `rich_math`, `rich_anchor`, `rich_thinking`
- `rich_img`, `rich_emoji`, `rich_emoji_markdown`, `rich_text_custom_emoji`, `register_custom_emoji`
- `register_custom_emojis`, `clear_custom_emojis`, `custom_emoji_names`, `rich_emoji_named`, `expand_emoji_shortcodes`
- `fetch_custom_emoji`, `rich_button`, `rich_button_row`, `rich_to_plain`, `rich_caption`
- `add_html_hook`, `clear_html_hooks`, `rich_send`, `rich_send_blocks`, `rich_reply`
- `rich_edit`, `rich_edit_inline`, `rich_answer`, `ephemeral_edit`, `ephemeral_delete`
- `RichDraft`

## Tests

```bash
pip install -e '.[test]'
pytest
```

Live integration tests require Telegram credentials.

## Credits

[Kurigram](https://github.com/kurigram-org/kurigram) — rich message support in the Pyrogram ecosystem.

NEXTGRAM by [BadmundaXd](https://t.me/BadmundaXd). MIT License.
