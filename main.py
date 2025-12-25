import os
import sys
from pyrogram import Client, idle
from flask import Flask
from threading import Thread
from config import API_ID, API_HASH, BOT_TOKEN, PORT, LOG_CHANNEL

# Path Fix (taki db.py aur config.py mil sakein)
sys.path.append(os.getcwd())

# Flask for Server Port Binding (For 24/7 Hosting)
web = Flask(__name__)
@web.route('/')
def home(): return "Bot is Alive!"

def run_web():
    web.run(host="0.0.0.0", port=PORT)

# Bot Client Setup
app = Client(
    "DogeshS4S",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins")
)

if __name__ == "__main__":
    # 1. Flask server start karo
    Thread(target=run_web).start()
    print(f"🚀 Web Server started on port {PORT}")

    # 2. Bot ko manually start karo
    app.start()
    print("🤖 Bot is starting...")

    # 3. Log Channel mein Alert bhejo
    try:
        me = app.get_me() # Bot ki info nikalne ke liye
        app.send_message(
            chat_id=LOG_CHANNEL,
            text=(f"🚀 **Bot Status Alert**\n\n"
                  f"👤 **Name:** {me.first_name}\n"
                  f"🆔 **ID:** `{me.id}`\n"
                  f"🌐 **Username:** @{me.username}\n"
                  f"✅ **Status:** Online & Ready!")
        )
        print("✅ Startup alert sent to Log Channel!")
    except Exception as e:
        print(f"❌ Log Alert Error: {e}")

    # 4. Bot ko running state mein rakho
    print("✅ Bot is fully running now!")
    idle()

    # 5. Stop hone par safely close karo
    app.stop()
