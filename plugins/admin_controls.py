from pyrogram import Client, filters
from db import users, orders, is_admin
from config import ADMIN_IDS, LOG_CHANNEL, JOIN_REWARD
from bson import ObjectId

# ================= 1. ADD CREDITS BY USER ID =================
# Usage: /addcredit 7273593616 1000
@Client.on_message(filters.command("addcredit") & filters.private)
async def add_credit_by_id(bot, m):
    # Admin check
    if not await is_admin(m.from_user.id):
        return

    if len(m.command) < 3:
        return await m.reply("❌ **Format:** `/addcredit [UserID] [Amount]`\nExample: `/addcredit 7273593616 1000`")

    try:
        target_id = int(m.command[1])
        amount = int(m.command[2])
        
        # User check in DB
        user = await users.find_one({"user_id": target_id})
        if not user:
            return await m.reply("❌ Ye User ID database mein nahi mili!")

        # Credits update
        await users.update_one({"user_id": target_id}, {"$inc": {"credits": amount}})
        
        # Admin ko reply
        await m.reply(f"✅ **Done!**\nUser `{target_id}` ko **{amount} Credits** bhej diye gaye hain.")
        
        # User ko notification
        try:
            await bot.send_message(target_id, f"🎁 **Admin Gift!**\n\nAdmin ne aapko **{amount} Credits** bheje hain. Enjoy! 🚀")
        except:
            pass

        # Log Channel Alert
        await bot.send_message(LOG_CHANNEL, f"💰 **Credits Added**\nAdmin: `{m.from_user.id}`\nUser: `{target_id}`\nAmt: {amount}")

    except ValueError:
        await m.reply("❌ UserID aur Amount hamesha numbers mein hone chahiye!")

# ================= 2. CANCEL ORDER BY USER ID =================
# Usage: /cancel_order 7273593616
# Ye command user ka sabse purana 'active' order cancel kar degi
@Client.on_message(filters.command("cancel_order") & filters.private)
async def cancel_order_by_user(bot, m):
    if not await is_admin(m.from_user.id):
        return

    if len(m.command) < 2:
        return await m.reply("❌ **Format:** `/cancel_order [UserID]`\nExample: `/cancel_order 7273593616`")

    try:
        target_id = int(m.command[1])
        
        # User ka sabse latest 'active' order dhundo
        order = await orders.find_one({"user_id": target_id, "status": "active"})
        
        if not order:
            return await m.reply(f"❌ User `{target_id}` ka koi bhi Active Order nahi mila!")

        # Logic: Partial Refund calculation
        remaining = order['subscribers'] - order['completed']
        refund = max(0, remaining * JOIN_REWARD)
        
        # 1. Update User Balance
        await users.update_one({"user_id": target_id}, {"$inc": {"credits": refund}})
        
        # 2. Update Order Status
        await orders.update_one({"_id": order['_id']}, {"$set": {"status": "cancelled"}})
        
        # Reply to Admin
        await m.reply(f"🛑 **Order Cancelled!**\n\nUser: `{target_id}`\nChannel: {order['title']}\nRefunded: {refund} Credits")
        
        # Notify User
        try:
            await bot.send_message(target_id, f"⚠️ Aapka order `{order['title']}` admin ne cancel kar diya hai. **{refund} credits** refund kar diye gaye hain.")
        except:
            pass
            
        # Log Alert
        await bot.send_message(LOG_CHANNEL, f"🛑 **Order Cancelled by ID**\nAdmin: `{m.from_user.id}`\nUser: `{target_id}`\nRefund: {refund}")

    except ValueError:
        await m.reply("❌ User ID numbers mein honi chahiye!")
