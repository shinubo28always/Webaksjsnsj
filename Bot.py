import os
from pyrogram import Client, filters
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = os.getenv("CHANNEL_USERNAME")
GROUP_ID = int(os.getenv("GROUP_ID"))

app = Client("anime_filter_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def search_anime(query):
    results = []
    async for message in app.search_messages(CHANNEL, query):
        if message.link:
            results.append(message.link)
    return results

@app.on_message(filters.chat(GROUP_ID) & filters.text)
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
