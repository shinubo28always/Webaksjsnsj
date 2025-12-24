from pyrogram import Client, filters
from db import users, orders, get_user
from config import MIN_ORDER_CREDITS, JOIN_REWARD, LOG_CHANNEL, ADMIN_IDS, ADMIN_ALERT, ORDER_SUCCESS

@Client.on_callback_query(filters.regex("^add$"))
async def add_btn_handler(bot, cb):
    await cb.message.edit_text("Apne channel ka Username (@username) ya Private ID bhejein.\n\n⚠️ Bot ka admin hona zaruri hai!")

@Client.on_message(filters.private & filters.text & ~filters.command(["start", "admin"]))
async def process_order(bot, m):
    uid = m.from_user.id
    user = await get_user(uid)
    
    if user['credits'] < MIN_ORDER_CREDITS:
        return await m.reply(f"Minimum {MIN_ORDER_CREDITS} credits chahiye order ke liye!")

    try:
        chat = await bot.get_chat(m.text)
        bot_member = await bot.get_chat_member(chat.id, "me")
        if not bot_member.privileges:
            return await m.reply("❌ Bot us channel me Admin nahi hai!")
        
        # Calculate Subscribers
        subs = user['credits'] // JOIN_REWARD
        credits_to_use = subs * JOIN_REWARD
        
        # Link nikalna
        link = f"https://t.me/{chat.username}" if chat.username else await bot.export_chat_invite_link(chat.id)
        
        order_data = {
            "user_id": uid,
            "title": chat.title,
            "channel_id": chat.id,
            "link": link,
            "subscribers": subs,
            "completed": 0,
            "status": "active"
        }
        
        res = await orders.insert_one(order_data)
        await users.update_one({"user_id": uid}, {"$inc": {"credits": -credits_to_use}})
        
        # Success Message
        await m.reply(ORDER_SUCCESS.format(subs=subs, credits=credits_to_use))
        
        # Log Channel Post
        await bot.send_message(LOG_CHANNEL, f"📢 **Naya Order!**\nChannel: {chat.title}\nSubs: {subs}\nID: `{res.inserted_id}`")
        
        # Admin Alert
        for adm in ADMIN_IDS:
            await bot.send_message(adm, ADMIN_ALERT.format(uid=uid, title=chat.title, subs=subs))
            
    except Exception as e:
        await m.reply(f"❌ Error: Channel nahi mila ya bot admin nahi hai. Details: {e}")
