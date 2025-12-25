import os
import sys
import asyncio
from pyrogram import Client, idle
from pyrogram.errors import FloodWait
from flask import Flask
from threading import Thread

# Config file se variables uthao
from config import API_ID, API_HASH, BOT_TOKEN, PORT, LOG_CHANNEL

# Path Fix (Importing db.py correctly)
sys.path.append(os.getcwd())

# ================= 1. FLASK SETUP (For 24/7 Hosting) =================
web = Flask(__name__)

@web.route('/')
def home():
    return "DogeshBhai S4S Bot is Online!"

def run_web():
    web.run(host="0.0.0.0", port=PORT)

# ================= 2. BOT CLIENT SETUP =================
app = Client(
    "DogeshS4S",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins")
)

async def start_bot():
    # A. Flask Server Start
    Thread(target=run_web).start()
    print(f"🚀 Web Server started on port {PORT}")

    # B. Start Bot with FloodWait Handling
    try:
        await app.start()
        me = await app.get_me() # Bot ki info fetch karega
        print(f"🤖 Bot Started: @{me.username}")

        # C. LOG CHANNEL ALERT (Jab bot start ho)
        log_text = (
            "🚀 **Bot Started Successfully!**\n\n"
            f"👤 **Name:** {me.first_name}\n"
            f"🆔 **ID:** `{me.id}`\n"
            f"🌐 **Username:** @{me.username}\n\n"
            "✅ **Status:** All systems operational!"
        )
        
        try:
            await app.send_message(LOG_CHANNEL, log_text)
            print("✅ Startup alert sent to Log Channel!")
        except Exception as log_err:
            print(f"❌ Could not send log alert: {log_err}")

        # D. Keep Bot Alive
        await idle()

    except FloodWait as e:
        print(f"⚠️ Telegram FloodWait: {e.value} seconds wait karna hoga...")
        await asyncio.sleep(e.value)
        await start_bot() # Wait ke baad phir se retry karega

    except Exception as e:
        print(f"❌ Startup Error: {e}")

    finally:
        # Safely Stop
        await app.stop()

# ================= 3. RUN THE BOT =================
if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(start_bot())
    except KeyboardInterrupt:
        print("🛑 Bot Stopped by Admin!")
