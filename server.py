import os
import time
from flask import Flask
from threading import Thread
from pyrogram import Client, filters, idle
from pyrogram.raw import functions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", 0))
PORT = int(os.getenv("PORT", 5000))

# Start message for /start command
START_MSG = """
👋 Hi {mention},

I am your **Anime Auto Video Bot** 🤖
Forward a video in any channel I am admin in, and I will automatically repost it with a custom caption.

⚡ Powered By: @AniReal_Team
"""

# Flask app for keep-alive
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "🤖 Anime Auto Video Bot is Running!"

def run_flask():
    flask_app.run(host="0.0.0.0", port=PORT)

# Pyrogram bot
app = Client("anime_video_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# /start command
@app.on_message(filters.command("start"))
async def start_command(client, message):
    mention = message.from_user.mention if message.from_user else "there"
    await message.reply_text(START_MSG.format(mention=mention))

# Forwarded video handler in any channel where bot is admin
@app.on_message(filters.video & filters.forwarded)
async def handle_forwarded_video(client, message):
    try:
        chat = message.chat
        # Check if bot is admin
        member = await client.get_chat_member(chat.id, "me")
        if not (member.status in ["administrator", "creator"]):
            return

        # Custom caption
        custom_caption = "Title - <anime_name>\nEpisode : <episode_number>\nSeason : <season_number>"

        # Repost video
        await client.send_video(chat_id=chat.id, video=message.video.file_id, caption=custom_caption)
        await message.delete()
    except Exception as e:
        print(f"Error in {chat.title or chat.id}: {e}")

# Notify owner
async def notify_owner():
    try:
        # Ensure proper time sync
        await app.send(functions.Ping(ping_id=int(time.time() * 1e6)))
        await app.send_message(OWNER_ID, "✅ Bot is now online")
    except Exception as e:
        print("Owner notify failed:", e)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    app.start()
    app.loop.create_task(notify_owner())
    idle()
    app.stop()
