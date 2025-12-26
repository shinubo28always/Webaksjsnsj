from pyrogram import Client, filters
from config import LOG_CHANNEL
from db import get_user_data

@Client.on_message(filters.private & filters.text & ~filters.command(["start", "admin", "orders", "addcredit", "cancel_order"]))
async def gatekeeper(bot, m):
    user_data = await get_user_data(m.from_user.id)
    # Agar user kuch process kar raha hai toh skip
    if user_data and user_data.get("step") is not None:
        return

    # Forward to Log Channel
    try:
        # Forward message with user info
        await m.forward(LOG_CHANNEL)
    except Exception as e:
        print(f"Log Error: {e}")
