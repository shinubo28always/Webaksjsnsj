import asyncio
from pyrogram import Client, filters
from pyrogram.types import ForceReply, InlineKeyboardMarkup, InlineKeyboardButton
from db import users, orders, get_user, get_user_data, set_step
from config import *
from bson import ObjectId

# --- STEP 1: ADD BUTTON (Force Reply) ---
@Client.on_callback_query(filters.regex("^add$"))
async def add_btn(bot, cb):
    await set_step(cb.from_user.id, "WAIT_CHANNEL")
    # ForceReply se keyboard open ho jayega
    await bot.send_message(
        chat_id=cb.from_user.id,
        text="📢 **Add Channel**\n\nApne channel ka Username (@username) ya Private ID is message ka **Reply** karke bhejien.",
        reply_markup=ForceReply(placeholder="@username or -100...")
    )
    await cb.answer()

# --- STEP 2: PROCESS CHANNEL (Analysing -> Connecting) ---
@Client.on_message(filters.private & filters.text & ~filters.command(["start", "admin", "orders", "addcredit", "cancel_order"]))
async def handle_inputs(bot, m):
    uid = m.from_user.id
    user_data = await get_user_data(uid)
    step = user_data.get("step")

    # A. Channel Input Handling
    if step == "WAIT_CHANNEL":
        msg = await m.reply("🔍 **Analysing...**")
        await asyncio.sleep(1)
        await msg.edit("⚡ **Connecting...**")
        await asyncio.sleep(1)

        try:
            chat_id = m.text.strip()
            # ID fix: Check if it's numeric
            if chat_id.startswith("-100") or (chat_id.replace("-", "").isdigit()):
                chat_id = int(chat_id)
            
            chat = await bot.get_chat(chat_id)
            bot_member = await bot.get_chat_member(chat.id, "me")
            
            if not bot_member.privileges:
                return await msg.edit("❌ **Error:** Bot us channel me Admin nahi hai! Pehle admin banayein.")

            # Save temp data and move to next step
            temp_info = {
                "chat_id": chat.id,
                "title": chat.title,
                "link": f"https://t.me/{chat.username}" if chat.username else await bot.export_chat_invite_link(chat.id)
            }
            await set_step(uid, "WAIT_CREDITS", temp_info)
            
            await msg.edit(
                f"✅ **Connected Successfully!**\n\n📢 **Channel:** {chat.title}\n💰 **Your Balance:** {user_data['credits']} Credits\n\nKitne credits use karna chahte hain? (Min: 50)\n\n_Example: 100_"
            )

        except Exception as e:
            await msg.edit(f"❌ **Connection Failed!**\n\nDetails: `{e}`\n\nDobara koshish karein ya Admin ko contact karein.")
            await set_step(uid, None)

    # B. Credits Input Handling
    elif step == "WAIT_CREDITS":
        if not m.text.isdigit():
            return await m.reply("❌ Sirf numbers bhejien!")
        
        amt = int(m.text)
        if amt < 50:
            return await m.reply("❌ Minimum 50 credits hona chahiye!")
        
        if amt > user_data['credits']:
            return await m.reply(f"❌ Low Balance! Aapke paas sirf {user_data['credits']} credits hain.")

        temp = user_data.get("temp_data")
        subs = amt // 2
        
        o_data = {
            "user_id": uid, "title": temp['title'], "channel_id": temp['chat_id'], 
            "link": temp['link'], "subscribers": subs, "completed": 0, "status": "active"
        }
        
        res = await orders.insert_one(o_data)
        await users.update_one({"user_id": uid}, {"$inc": {"credits": -amt}, "$set": {"step": None, "temp_data": None}})
        
        await m.reply(ORDER_SUCCESS.format(title=temp['title'], subs=subs, credits=amt))
        
        # LOG CHANNEL NOTIFICATION
        log_msg = (f"🆕 **New Order Placed**\n\n"
                   f"👤 User: `{uid}`\n"
                   f"📢 Channel: {temp['title']}\n"
                   f"👥 Target: {subs} Subs\n"
                   f"💰 Cost: {amt} Credits")
        try:
            await bot.send_message(LOG_CHANNEL, log_text=log_msg)
        except: pass
