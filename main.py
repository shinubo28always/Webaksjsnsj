import os
import sys
import asyncio
from pyrogram import Client, idle
from pyrogram.errors import FloodWait
from flask import Flask
from threading import Thread

# Config file se variables uthao
from config import API_ID, API_HASH, BOT_TOKEN, PORT, LOG_CHANNEL

# Essential Fix: Taki bot db.py aur config.py ko asani se dhund sake
sys.path.append(os.getcwd())

# ================= 1. FLASK WEB SERVER =================
# Ye Render/Koyeb jaise servers par 24/7 hosting ke liye zaruri hai
web = Flask(__name__)

@web.route('/')
def home():
    return "DogeshBhai S4S Bot is Online and Running!"

def run_web():
    web.run(host="0.0.0.0", port=PORT)

# ================= 2. PYROGRAM BOT CLIENT =================
app = Client(
    "DogeshS4S",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins") # plugins folder se sari files auto-load hongi
)

async def start_bot():
    # A. Flask Server ko alag thread me start karo
    Thread(target=run_web).start()
    print(f"🚀 Flask Web Server started on port {PORT}")

    try:
        # B. Telegram Client ko start karo
        await app.start()
        me = await app.get_me()
        print(f"🤖 Bot Started: @{me.username}")

        # C. LOG CHANNEL STARTUP ALERT
        try:
            # Ensure LOG_CHANNEL is an integer
            log_id = int(LOG_CHANNEL)
            startup_text = (
                "🚀 **Bot Startup Alert**\n\n"
                f"👤 **Bot Name:** {me.first_name}\n"
                f"🆔 **Bot ID:** `{me.id}`\n"
                f"🌐 **Username:** @{me.username}\n\n"
                "✅ **Status:** Online & Ready to Work!"
            )
            await app.send_message(chat_id=log_id, text=startup_text)
            print("✅ Log Channel startup alert sent!")
        except Exception as log_err:
            print(f"⚠️ Could not send log alert: {log_err}")

        print("✅ Bot is fully operational. Waiting for users...")
        
        # D. Bot ko running state me rakho
        await idle()

    except FloodWait as e:
        # Agar Telegram rate limit lagaye toh wait karega
        print(f"⚠️ FloodWait: Waiting for {e.value} seconds...")
        await asyncio.sleep(e.value)
        await start_bot() # Wait ke baad phir se start karega

    except Exception as e:
        print(f"❌ Startup Error: {e}")

    finally:
        # Safely shutdown
        await app.stop()

# ================= 3. EXECUTION =================
if __name__ == "__main__":
    try:
        # Async loop ke sath bot run karo
        asyncio.get_event_loop().run_until_complete(start_bot())
    except KeyboardInterrupt:
        print("🛑 Bot stopped manually by admin.")
