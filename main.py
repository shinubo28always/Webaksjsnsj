import asyncio
from pyrogram import Client
from flask import Flask
from threading import Thread
from config import *

# Flask app for hosting port binding
web = Flask(__name__)

@web.route('/')
def home():
    return "Bot is Running!"

def run_flask():
    web.run(host="0.0.0.0", port=PORT)

# Pyrogram Client with Plugins
app = Client(
    "SubXBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins") # Ye line sare plugins automatic load karegi
)

if __name__ == "__main__":
    # Start Flask in a separate thread
    Thread(target=run_flask).start()
    print("✅ Flask Server Started on Port:", PORT)
    
    # Start Bot
    print("🤖 Bot is starting...")
    app.run()
