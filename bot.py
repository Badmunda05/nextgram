
import os
import random

from pyrogram import Client, filters

from nextgram import (
    RICH_AVAILABLE,
    rich_button,
    rich_button_row,
    rich_details_group,
    rich_edit,
    rich_emoji_named,
    rich_heading,
    rich_kv_table,
    rich_note,
    rich_page_index,
    rich_pre_rich,
    rich_reply,
    rich_todo_list,
    register_custom_emoji,
)

from nextgram.widgets import send_widget


register_custom_emoji("fire", "5368324170671202286", "🔥")

STYLES = ("primary", "success", "danger")


def random_style() -> str:
    return random.choice(STYLES)


def home_text() -> str:
    return (
        rich_heading("NEXTGRAM Demo", level=3)
        + rich_note(
            "Buttons change colour every time you tap Shuffle. "
            + rich_emoji_named("fire")
        )
        + rich_kv_table([
            ("Library", "NEXTGRAM"),
            ("Rich support", "yes" if RICH_AVAILABLE else "no"),
            ("Widget test", "/widget"),
        ])
        + rich_todo_list([
            ("Clone nextgram", True),
            ("Try the demo bot", True),
            ("Build your own checklist", False),
        ])
        + rich_details_group([
            ("What is this?", "A test bot for the NEXTGRAM package."),
            ("HTML Widgets", "Send /widget to test HTML widgets."),
        ], open_first=True)
        + rich_pre_rich(
            "<b>pip</b> install <code>nextgram</code>",
            language="bash",
        )
        + rich_page_index(1, 1, total=3, label="Demo")
    )


def home_kb() -> str:
    return (
        rich_button_row(
            rich_button(
                "🎨 Shuffle colours",
                callback_data="shuffle",
                style=random_style(),
            ),
            rich_button(
                "🏓 Ping",
                callback_data="ping",
                style=random_style(),
            ),
            rich_button(
                "📋 Copy repo",
                copy_text="https://github.com/Badmunda05/nextgram",
                style=random_style(),
            ),
        )
        + rich_button_row(
            rich_button(
                "🧩 Test Widget",
                callback_data="widget",
                style="primary",
            ),
            rich_button(
                "🍬 Support",
                url="https://t.me/BadmundaXd",
                style=random_style(),
            ),
        )
        + rich_button_row(
            rich_button(
                "⌯ Close ⌯",
                callback_data="close",
                style="danger",
            ),
        )
    )


async def start(_, message):
    await rich_reply(message, home_text() + home_kb())


async def shuffle(_, cbq):
    await rich_edit(cbq, home_text() + home_kb())
    await cbq.answer("Colours shuffled")


async def ping(_, cbq):
    await cbq.answer("Pong!", show_alert=True)


async def close(_, cbq):
    await cbq.answer()
    await cbq.message.delete()


async def send_demo_widget(client, chat_id):
    html = """
    <div style="text-align:center;padding:16px">
        <h2>🔥 NEXTGRAM</h2>
        <p>Bot API 10.4</p>
        <hr>
        <h3>HTML Widget Demo</h3>
        <p>Powered by NEXTGRAM</p>
        <button>Tap Me</button>
    </div>
    """

    await send_widget(
        client,
        chat_id,
        html,
        token=os.environ["BOT_TOKEN"],
    )


async def widget(client, message):
    try:
        await send_demo_widget(client, message.chat.id)
    except Exception as e:
        print(f"Widget error: {e}")
        await message.reply_text(
            "❌ Widget test failed. Check bot logs."
        )


async def widget_callback(client, cbq):
    await cbq.answer("Loading widget...")

    try:
        await send_demo_widget(client, cbq.message.chat.id)
    except Exception as e:
        print(f"Widget error: {e}")
        await cbq.message.reply_text(
            "❌ Widget test failed. Check bot logs."
        )


def create_app() -> Client:
    app = Client(
        "nextgram_demo",
        api_id=int(os.environ["API_ID"]),
        api_hash=os.environ["API_HASH"],
        bot_token=os.environ["BOT_TOKEN"],
        in_memory=True,
    )

    app.on_message(filters.command("start"))(start)
    app.on_message(filters.command("widget"))(widget)

    app.on_callback_query(filters.regex("^shuffle$"))(shuffle)
    app.on_callback_query(filters.regex("^ping$"))(ping)
    app.on_callback_query(filters.regex("^close$"))(close)
    app.on_callback_query(filters.regex("^widget$"))(widget_callback)

    return app


if __name__ == "__main__":
    print("NEXTGRAM demo bot started!")
    create_app().run()
    
