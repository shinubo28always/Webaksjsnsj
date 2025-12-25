from pyrogram import Client, filters
from config import LOG_CHANNEL
from db import get_user_data

@Client.on_message(filters.private & filters.text & ~filters.command(["start", "admin", "orders", "addcredit", "cancel_order", "add_admin", "del_admin", "broadcast", "pbroadcast", "tbroadcast"]))
async def gatekeeper(bot, m):
    user_data = await get_user_data(m.from_user.id)
    step = user_data.get("step")
    
    # Agar user koi process (Add Channel/Credits) nahi kar raha tabhi forward karo
    if not step:
        try:
            await m.forward(LOG_CHANNEL)
            # User ko msg bhi bhej sakte ho (Optional)
        except Exception as e:
            print(f"Log Error: {e}")
