import os
import sys
from pyrogram import Client
from flask import Flask
from threading import Thread
from config import API_ID, API_HASH, BOT_TOKEN, PORT

# --- YE FIX HAI: Root path add karo ---
sys.path.append(os.getcwd()) 

# Flask for Server Port Binding
web = Flask(__name__)
@web.route('/')
def home(): return "Bot is Alive!"

def run_web():
    web.run(host="0.0.0.0", port=PORT)

# Bot Client
app = Client(
    "SubXBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins")
)

if __name__ == "__main__":
    Thread(target=run_web).start()
    print(f"🚀 Web Server started on port {PORT}")
    print("🤖 Bot is starting...")
    app.run()
