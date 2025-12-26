from pyrogram import Client, filters
from pyrogram.types import ForceReply
from db import get_user, set_step, get_user_data
from config import *
import asyncio

@Client.on_callback_query(filters.regex("^add$"))
async def add_btn(bot, cb):
    uid = cb.from_user.id
    await set_step(uid, "WAIT_CH")
    await bot.send_message(
        uid, 
        "📢 **Add Channel**\n\nApne channel ka Username (@username) ya ID bhejien.",
        reply_markup=ForceReply(True)
    )

@Client.on_message(filters.private & filters.text & ~filters.command(["start", "admin", "orders"]))
async def process_orders(bot, m):
    uid = m.from_user.id
    user_data = await get_user_data(uid)
    if not user_data or user_data.get("step") is None:
        return # Gatekeeper handles this

    step = user_data.get("step")

    if step == "WAIT_CH":
        msg = await m.reply("🔍 **Connecting to Channel...**")
        try:
            input_data = m.text.strip()
            # Numeric ID fix
            if input_data.startswith("-100") or input_data.replace("-","").isdigit():
                input_data = int(input_data)
            
            # Yahan bot chat ko resolve karega
            chat = await bot.get_chat(input_data)
            bot_stat = await bot.get_chat_member(chat.id, "me")
            
            if not bot_stat.privileges:
                return await msg.edit("❌ Bot admin nahi hai!")

            temp = {
                "chat_id": chat.id,
                "title": chat.title,
                "link": f"https://t.me/{chat.username}" if chat.username else await bot.export_chat_invite_link(chat.id)
            }
            await set_step(uid, "WAIT_CR", temp)
            await msg.edit(f"✅ **Connected:** {chat.title}\n\nKitne credits use karne hain? (Min 50)\nNote: 2 Credits = 1 Subscriber")

        except Exception as e:
            await msg.edit(f"❌ **Error:** Bot ko channel nahi mila.\n\n**Solution:** Channel me ek message bhejein aur phir yahan ID dalein.\nDetail: `{e}`")

    elif step == "WAIT_CR":
        if not m.text.isdigit(): return await m.reply("Numbers only!")
        amt = int(m.text)
        if amt < 50 or amt > user_data['credits']:
            return await m.reply("Invalid Amount!")

        temp = user_data.get("temp_data")
        subs = amt // 2
        
        from db import orders, users
        from bson import ObjectId
        
        order_obj = {
            "user_id": uid, "title": temp['title'], "channel_id": temp['chat_id'],
            "link": temp['link'], "subscribers": subs, "completed": 0, "status": "active"
        }
        await orders.insert_one(order_obj)
        await users.update_one({"user_id": uid}, {"$inc": {"credits": -amt}, "$set": {"step": None, "temp_data": None}})
        
        await m.reply(f"✅ **Order Placed!**\nChannel: {temp['title']}\nSubs: {subs}")
        
        # LOG CHANNEL NOTIFY
        try:
            await bot.send_message(LOG_CHANNEL, f"🆕 **New Order!**\nUser: `{uid}`\nChannel: {temp['title']}")
        except: pass
