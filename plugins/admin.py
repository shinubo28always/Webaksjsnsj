from pyrogram import Client, filters
from db import users, orders
from config import ADMIN_IDS

@Client.on_message(filters.command("admin") & filters.user(ADMIN_IDS))
async def admin_panel(bot, m):
    await m.reply("👑 **Admin Panel**\n\n/stats - Bot ki report\n/addcredits [ID] [Amt] - Credits dene ke liye\n/cancel [OrderID] - Order rokne ke liye")

@Client.on_message(filters.command("stats") & filters.user(ADMIN_IDS))
async def stats_handler(bot, m):
    total_u = await users.count_documents({})
    total_o = await orders.count_documents({"status": "active"})
    await m.reply(f"📊 **Stats:**\nTotal Users: {total_u}\nActive Orders: {total_o}")

@Client.on_message(filters.command("addcredits") & filters.user(ADMIN_IDS))
async def add_creds_adm(bot, m):
    try:
        _, uid, amt = m.text.split()
        await users.update_one({"user_id": int(uid)}, {"$inc": {"credits": int(amt)}})
        await m.reply(f"✅ Done! {amt} credits added to {uid}")
        await bot.send_message(int(uid), f"🎁 Admin ne aapko {amt} credits bheje hain!")
    except:
        await m.reply("Usage: `/addcredits [UserID] [Amount]`")

@Client.on_message(filters.command("cancel") & filters.user(ADMIN_IDS))
async def cancel_order_adm(bot, m):
    try:
        from bson import ObjectId
        oid = m.text.split()[1]
        await orders.update_one({"_id": ObjectId(oid)}, {"$set": {"status": "cancelled"}})
        await m.reply("✅ Order cancelled successfully!")
    except:
        await m.reply("Usage: `/cancel [OrderID]`")
