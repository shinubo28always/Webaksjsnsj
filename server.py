from flask import Flask
from threading import Thread
import bot  # Import the Pyrogram bot

app = Flask(__name__)

@app.route("/")
def home():
    return "🤖 Anime Auto Search Bot is Running!"

def run():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

# Start Flask in a thread
t = Thread(target=run)
t.start()

# Start Pyrogram bot
bot.app.run()
