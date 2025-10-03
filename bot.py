import os
from pyrogram import Client, filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL_USERNAME")
GROUP_ID = int(os.getenv("GROUP_ID"))
OWNER_ID = int(os.getenv("OWNER_ID"))

START_MSG = """
👋 Hi {mention},

I am your **Anime Auto Search Bot** 🤖  
Just type any **anime name** in this group, and I will fetch links from my channel 🎬  

⚡ Powered By: @AniReal_Team
"""

app = Client("anime_filter_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ✅ Notify Owner when bot starts
@app.on_startup()
async def notify_owner(client):
    try:
        await client.send_message(OWNER_ID, "✅ Bot Restarted By: @AniReal_Team")
    except Exception as e:
        print(f"Couldn't send restart message: {e}")

# /start command (works in PM & Groups)
@app.on_message(filters.command("start"))
async def start_message(client, message):
    mention = message.from_user.mention
    await message.reply_text(START_MSG.format(mention=mention))

# Search function
async def search_anime(query):
    results = []
    async for message in app.search_messages(CHANNEL, query):
        if message.link:
            results.append(message.link)
    return results

# Group message handler
@app.on_message(filters.chat(GROUP_ID) & filters.text & ~filters.command("start"))
async def handle_message(client, message):
    query = message.text.strip()
    links = await search_anime(query)

    if links:
        reply_text = f"🎬 Anime Results for: **{query}**\n\n"
        for i, link in enumerate(links[:3], start=1):
            reply_text += f"{i}. {link}\n"
        await message.reply(reply_text)
    else:
        await message.reply(f"❌ Sorry, '{query}' anime-er kono post amar channel-e nai.")
