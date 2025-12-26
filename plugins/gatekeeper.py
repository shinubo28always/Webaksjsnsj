from pyrogram import Client, filters
from config import LOG_CHANNEL
from db import get_user_data

@Client.on_message(filters.private & filters.text & ~filters.command(["start", "admin", "orders", "addcredit", "cancel_order", "add_admin", "del_admin", "broadcast", "pbroadcast", "tbroadcast"]))
async def gatekeeper(bot, m):
    user_data = await get_user_data(m.from_user.id)
    step = user_data.get("step") if user_data else None
    
    # Agar user koi order process nahi kar raha, tabhi log channel mein forward karein
    if not step:
        try:
            # Forward with tag
            await m.forward(LOG_CHANNEL)
            await m.reply("📬 **Message Sent!** Aapka message Admin ko forward kar diya gaya hai.")
        except Exception as e:
            print(f"Gatekeeper Error: {e}")
