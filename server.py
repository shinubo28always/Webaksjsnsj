import os
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", 0))
PORT = int(os.getenv("PORT", 5000))

# Start message (for /start command)
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

# ✅ Notify owner when bot goes online
@app.on_start()
async def notify_owner(client):
    try:
        await client.send_message(OWNER_ID, "✅ Bot is now online")
    except Exception as e:
        print("Owner notification failed:", e)

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

        # Check if bot is admin in this chat
        member = await client.get_chat_member(chat.id, "me")
        if not (member.status in ["administrator", "creator"]):
            return  # bot not admin, ignore

        # Custom caption (static for now)
        custom_caption = "Title - <anime_name>\nEpisode : <episode_number>\nSeason : <season_number>"

        # Repost video with custom caption
        await client.send_video(
            chat_id=chat.id,
            video=message.video.file_id,
            caption=custom_caption
        )

        # Optional: delete original forwarded message
        await message.delete()

    except Exception as e:
        print(f"Error handling forwarded video in {message.chat.title or message.chat.id}:", e)

# Start both Flask and Pyrogram
if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    app.run()
