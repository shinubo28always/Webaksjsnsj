from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread
from config import Config
import asyncio

# Flask app for keeping bot alive on Render
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is Alive on Render!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()


# Pyrogram Bot setup
bot = Client(
    "RenderBot",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH
)


# Send startup message to owner when bot comes online
async def send_startup_msg():
    try:
        await bot.send_message(
            chat_id=Config.OWNER_ID,
            text="✅ **Bot is Now Online and Running on Render!** 🚀"
        )
        print(f"✅ Startup message sent to owner ({Config.OWNER_ID})")
    except Exception as e:
        print(f"❌ Failed to send startup message: {e}")


# Start command (with photo + inline buttons)
@bot.on_message(filters.command("start") & filters.private)
async def start(_, message):
    me = await bot.get_me()
    buttons = [
        [
            InlineKeyboardButton(
                "➕ Connect Your Group",
                url=f"https://t.me/{me.username}?startgroup=true"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 Join Our Update Channel",
                url="https://t.me/YourUpdateChannel"  # replace with your real channel link
            )
        ]
    ]
    
    await message.reply_photo(
        photo="https://telegra.ph/file/2cfa3dc3b3b6f2d417b23.jpg",  # replace with your image
        caption=(
            "**👋 Hey Boss!**\n\n"
            "I'm your friendly assistant bot 🤖\n"
            "Add me to your group and make moderation easy & fun!"
        ),
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# Run Flask + Bot together
if __name__ == "__main__":
    keep_alive()
    print("🚀 Bot is running on Render...")

    async def start_bot():
        await bot.start()
        await send_startup_msg()  # Notify owner
        print("✅ Bot started successfully!")
        await idle()  # Keep running

    from pyrogram import idle
    asyncio.run(start_bot())
