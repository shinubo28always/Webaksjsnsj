import os
import sys
import asyncio
from pyrogram import Client, idle
from flask import Flask
from threading import Thread
from config import API_ID, API_HASH, BOT_TOKEN, PORT, LOG_CHANNEL

sys.path.append(os.getcwd())

web = Flask(__name__)
@web.route('/')
def home(): return "Bot is Online!"

def run_web():
    web.run(host="0.0.0.0", port=PORT)

app = Client(
    "DogeshS4S",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins")
)

async def start_bot():
    Thread(target=run_web).start()
    await app.start()
    
    # --- LOG CHANNEL RESOLUTION FIX ---
    try:
        # Bot pehle log channel ko cache me save karega
        log_chat = await app.get_chat(int(LOG_CHANNEL))
        await app.send_message(log_chat.id, "🚀 **Bot Startup Alert!**\nSari systems active hain.")
        print(f"✅ Log Channel Connected: {log_chat.title}")
    except Exception as e:
        print(f"❌ Log Channel Error: {e}. Check karein ki bot wahan admin hai ya nahi.")

    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(start_bot())
