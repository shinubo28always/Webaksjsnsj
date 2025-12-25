from pyrogram import Client, filters
from config import LOG_CHANNEL, ADMIN_IDS
from db import get_step

@Client.on_message(filters.private & filters.text & ~filters.command(["start", "admin", "orders", "addcredit", "cancel_order", "add_admin", "del_admin", "broadcast", "pbroadcast", "tbroadcast"]))
async def forward_random_messages(bot, m):
    uid = m.from_user.id
    step = await get_step(uid)
    
    # Agar user kisi step (jaise add_channel) mein nahi hai, toh msg forward karo
    if step is None:
        # 1. Admin ko forward karo with tag
        await m.forward(LOG_CHANNEL)
        
        # 2. User ko batao (Optional)
        await m.reply("⚠️ Ye koi valid command nahi hai. Aapka message Admin ko bhej diya gaya hai.")

# Forward tags ke sath message bhejta hai automatically .forward() use karne par.
