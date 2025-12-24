import os
from dotenv import load_dotenv

load_dotenv()

# --- Config Logic: Server Env > .env > Default ---
def get_env(key, default=None):
    return os.getenv(key, default)

# Bot API Credentials
API_ID = int(get_env("API_ID", "12345"))
API_HASH = get_env("API_HASH", "your_hash")
BOT_TOKEN = get_env("BOT_TOKEN", "your_token")
MONGO_URL = get_env("MONGO_URL", "mongodb://...")

# IDs
ADMIN_IDS = [int(x) for x in get_env("ADMIN_IDS", "").split(",")]
LOG_CHANNEL = int(get_env("LOG_CHANNEL", "-100..."))

# Values
JOIN_REWARD = int(get_env("JOIN_REWARD", 2))
REF_REWARD = int(get_env("REF_REWARD", 5))
PENALTY_CREDITS = int(get_env("PENALTY_CREDITS", 10))
MIN_ORDER_CREDITS = int(get_env("MIN_ORDER_CREDITS", 50))
PORT = int(get_env("PORT", 8080))

# --- MESSAGES & TEXTS ---
START_MSG = "👋 **Welcome to SubXChange!**\n\n💰 Balance: `{bal}` Credits\n\nInvite friends or join channels to earn!"
EARN_MSG = "Join this channel to earn {reward} credits:\n\n📌 **{title}**"
ORDER_SUCCESS = "✅ **Order Placed!**\n\nTarget: {subs} Subscribers.\nCredits Deducted: {credits}"
PENALTY_MSG = "❌ **Penalty Alert!**\n\nAapne `{title}` leave kiya jabki order active tha. **-{penalty} Credits** cut gaye."
REFER_MSG = "🔗 **Refer & Earn**\n\nShare this link: `https://t.me/{username}?start={uid}`\n\nHar referral par milenge **{reward} Credits**!"
NOT_JOINED_MSG = "⚠️ Pehle channel join karo phir verify button dabao!"
ADMIN_ALERT = "🚀 **New Order Alert!**\n\nUser: `{uid}`\nChannel: {title}\nSubs: {subs}"
