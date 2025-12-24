import os
from dotenv import load_dotenv

# .env file load karo agar exist karti hai
load_dotenv()

# --- Smart Env Helper ---
def get_env(key, default=None):
    val = os.getenv(key)
    # Agar variable server setting me nahi hai ya khali choda gaya hai
    if val is None or val.strip() == "":
        return default
    return val.strip()

# ================= CREDENTIALS =================
# Server Settings > .env > Default Value
API_ID = int(get_env("API_ID", "28568452"))
API_HASH = get_env("API_HASH", "8439af0a8ecc67bca4859180e7f9c8b9")
BOT_TOKEN = get_env("BOT_TOKEN", "")
MONGO_URL = get_env("MONGO_URL", "")

# ================= SETTINGS & IDs =================
# Admin IDs ko list me convert karna (Comma separated input: "123,456")
admin_str = get_env("ADMIN_IDS", "7009167334")
ADMIN_IDS = [int(x) for x in admin_str.split(",") if x.strip().isdigit()]

LOG_CHANNEL = int(get_env("LOG_CHANNEL", "-1003202118558"))
PORT = int(get_env("PORT", "8080"))

# Rewards & Penalties
JOIN_REWARD = int(get_env("JOIN_REWARD", "2"))
REF_REWARD = int(get_env("REF_REWARD", "5"))
PENALTY_CREDITS = int(get_env("PENALTY_CREDITS", "10"))
MIN_ORDER_CREDITS = int(get_env("MIN_ORDER_CREDITS", "50"))

# ================= ASSETS (Stickers & Images) =================
# Kisi bot se Sticker ID nikal kar yahan dalein
START_STICKER = get_env("START_STICKER", "CAACAgUAAxkBAAEP4flpKC6Ozwtd25givMwrN3zMcnLeFQACuBYAArKmaFa__rW3azdtFjYE") 
START_IMG = get_env("START_IMG", "https://graph.org/file/fdc4357abfaba23255e98-24d1bbfa3888cdfcfe.jpg")

# ================= MESSAGES (Customizable) =================

START_MSG = """
👋 **Welcome to DogeshBhai S4S Bot!**

💰 **Balance:** `{bal}` Credits
🎁 **Refer Bonus:** `{ref}` Credits

Invite friends or join channels to grow your subscribers fast! 🚀
"""

HELP_MSG = """
❓ **Kaise Kaam Karta Hai?**

1️⃣ **Earn:** 'Earn' button dabayein aur channels join karein.
2️⃣ **Verify:** Join karne ke baad verify karein, credits mil jayenge.
3️⃣ **Add:** Credits hone par apna channel add karein.
4️⃣ **Penalty:** Agar active order leave kiya toh credits cut jayenge!

**Note:** Bot aapke channel me Admin hona chahiye.
"""

ABOUT_MSG = """
🤖 **Bot Info**

• **Name:** DogeshBhai S4S
• **Language:** Python (Pyrogram)
• **Database:** MongoDB
• **Hosting:** Modular Port Binding
• **Dev:** @DogeshBhai_Pure_Bot
"""

EARN_MSG = """
Join this channel to earn **{reward}** credits:

📢 **{title}**

Join karne ke baad niche verify button dabayein. 👇
"""

ORDER_SUCCESS = """
✅ **Order Successful!**

📢 **Channel:** {title}
👥 **Target:** {subs} Subscribers
💰 **Used:** {credits} Credits

Aapka order live ho chuka hai!
"""

PENALTY_MSG = """
❌ **Penalty Alert!**

Aapne `{title}` leave kar diya hai jabki order active tha.
Isliye aapke **{penalty} Credits** cut kar liye gaye hain. ⚠️
"""

REFER_MSG = """
🔗 **Refer & Earn System**

Aapka link niche hai. Isse dosto ko invite karein:
`https://t.me/{username}?start={uid}`

Har friend ke join karne par aapko milenge **{reward} Credits!** 🎁
"""

NOT_JOINED_MSG = "⚠️ Aapne abhi join nahi kiya! Pehle join karein phir verify dabayein."

ADMIN_ALERT = "🚀 **New Order Alert!**\n\n👤 User: `{uid}`\n📢 Channel: {title}\n👥 Subs: {subs}"

# ======================================================
