from pyrogram import Client, filters
from flask import Flask
from threading import Thread
from config import Config

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

# Start command
@bot.on_message(filters.command("start") & filters.private)
async def start(_, message):
    await message.reply_text(
        "👋 Hello! Bot is running successfully on Render ⚡"
    )


# Run Flask + Bot together
if __name__ == "__main__":
    keep_alive()
    print("🚀 Bot is running on Render...")
    bot.run()
