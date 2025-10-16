from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread
from config import Config
import asyncio

# Flask setup for Render keep alive
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is Alive on Render!"

def run_flask():
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()


# Pyrogram Bot setup
bot = Client(
    "RenderBot",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH
)


@bot.on_message(filters.command("start") & filters.private)
async def start(_, message):
    me = await bot.get_me()
    buttons = [
        [InlineKeyboardButton("➕ Connect Your Group", url=f"https://t.me/{me.username}?startgroup=true")],
        [InlineKeyboardButton("📢 Join Our Update Channel", url="https://t.me/YourUpdateChannel")]  # Replace with real link
    ]
    await message.reply_photo(
        photo="https://telegra.ph/file/2cfa3dc3b3b6f2d417b23.jpg",
        caption=(
            "**👋 Hey Boss!**\n\n"
            "I'm your friendly assistant bot 🤖\n"
            "Add me to your group and make moderation easy & fun!"
        ),
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def main():
    await bot.start()
    print("✅ Pyrogram bot started successfully!")

    try:
        await bot.send_message(Config.OWNER_ID, "✅ Boss! Bot online hoye gese 🔥 Render e successfully run kortese 😎")
        print(f"📩 Owner PM sent to {Config.OWNER_ID}")
    except Exception as e:
        print(f"⚠️ Failed to send PM to owner: {e}")

    await idle()
    print("🛑 Bot stopped.")
    await bot.stop()


if __name__ == "__main__":
    keep_alive()  # Run Flask server
    asyncio.get_event_loop().run_until_complete(main())
