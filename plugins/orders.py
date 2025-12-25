from pyrogram import Client, filters
from db import users, orders, get_user, get_step, set_step
from config import *
from bson import ObjectId

@Client.on_callback_query(filters.regex("^add$"))
async def add_btn(bot, cb):
    await set_step(cb.from_user.id, "add_channel") # Step set kiya
    await cb.message.edit_text("Apne channel ka Username (@username) ya Private ID bhejein.\n\n⚠️ Bot ka admin hona zaruri hai!")

@Client.on_message(filters.private & filters.text & ~filters.command(["start", "admin", "orders", "addcredit", "cancel_order"]))
async def process_order(bot, m):
    uid = m.from_user.id
    step = await get_step(uid)
    
    # Sirf tabhi process karega jab user 'add_channel' step mein ho
    if step != "add_channel":
        return # Ye niche wale gatekeeper plugin mein handle hoga

    user = await get_user(uid)
    if user['credits'] < MIN_ORDER_CREDITS:
        await set_step(uid, None)
        return await m.reply(f"❌ Minimum {MIN_ORDER_CREDITS} credits chahiye!")

    try:
        # ID Fix: Agar numeric ID hai toh int() mein convert karega
        chat_id = m.text.strip()
        if chat_id.replace("-", "").isdigit():
            chat_id = int(chat_id)
            
        chat = await bot.get_chat(chat_id)
        bot_member = await bot.get_chat_member(chat.id, "me")
        
        if not bot_member.privileges:
            return await m.reply("❌ Bot us channel me Admin nahi hai!")
        
        subs = user['credits'] // JOIN_REWARD
        cost = subs * JOIN_REWARD
        link = f"https://t.me/{chat.username}" if chat.username else await bot.export_chat_invite_link(chat.id)
        
        o_data = {
            "user_id": uid, "title": chat.title, "channel_id": chat.id, 
            "link": link, "subscribers": subs, "completed": 0, "status": "active"
        }
        
        res = await orders.insert_one(o_data)
        await users.update_one({"user_id": uid}, {"$inc": {"credits": -cost}, "$set": {"step": None}}) # Step clear
        
        await m.reply(ORDER_SUCCESS.format(title=chat.title, subs=subs, credits=cost))
        await bot.send_message(LOG_CHANNEL, f"📢 **New Order!**\nChannel: {chat.title}\nSubs: {subs}\nID: `{res.inserted_id}`")
        
    except Exception as e:
        await m.reply(f"❌ **Error:** Channel nahi mila ya bot admin nahi hai.\n\nDetails: `{e}`")
