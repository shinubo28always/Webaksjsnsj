from pyrogram import Client, filters
from db import users, orders, get_user, get_user_data, set_step
from config import *
from bson import ObjectId

# --- STEP 1: ADD BUTTON ---
@Client.on_callback_query(filters.regex("^add$"))
async def add_btn(bot, cb):
    await set_step(cb.from_user.id, "WAIT_CHANNEL")
    await cb.message.edit_text("📢 **Add Channel**\n\nApne channel ka Username (@username) ya Private ID bhejien.\n\n⚠️ Bot ka admin hona zaruri hai!")

# --- STEP 2 & 3: PROCESS INPUTS ---
@Client.on_message(filters.private & filters.text & ~filters.command(["start", "admin", "orders", "addcredit", "cancel_order"]))
async def process_inputs(bot, m):
    uid = m.from_user.id
    user_data = await get_user_data(uid)
    step = user_data.get("step")

    # A. Channel Input Handle Karo
    if step == "WAIT_CHANNEL":
        try:
            chat_id = m.text.strip()
            if chat_id.startswith("-100") or chat_id.isdigit():
                chat_id = int(chat_id)
            
            chat = await bot.get_chat(chat_id)
            bot_member = await bot.get_chat_member(chat.id, "me")
            
            if not bot_member.privileges:
                return await m.reply("❌ Bot us channel me Admin nahi hai!")

            # Temporary data save karo aur credits pucho
            temp_info = {
                "chat_id": chat.id,
                "title": chat.title,
                "link": f"https://t.me/{chat.username}" if chat.username else await bot.export_chat_invite_link(chat.id)
            }
            await set_step(uid, "WAIT_CREDITS", temp_info)
            
            await m.reply(f"✅ **Channel Connected:** {chat.title}\n\nAb bataiye aap kitne credits use karna chahte hain?\n\n💰 **Your Balance:** {user_data['credits']}\n🔸 **Min Credits:** 50\n🔹 **Note:** 2 Credits = 1 Subscriber")

        except Exception as e:
            await m.reply(f"❌ Error: Channel nahi mila. Check karein ki bot admin hai ya nahi.\n`{e}`")

    # B. Credits Input Handle Karo
    elif step == "WAIT_CREDITS":
        if not m.text.isdigit():
            return await m.reply("❌ Sirf numbers bhejien!")
        
        amt = int(m.text)
        if amt < 50:
            return await m.reply("❌ Minimum 50 credits hona chahiye!")
        
        if amt > user_data['credits']:
            return await m.reply(f"❌ Aapke paas sirf {user_data['credits']} credits hain!")

        # Order confirm karo
        temp = user_data.get("temp_data")
        subs = amt // 2
        
        o_data = {
            "user_id": uid, "title": temp['title'], "channel_id": temp['chat_id'], 
            "link": temp['link'], "subscribers": subs, "completed": 0, "status": "active"
        }
        
        res = await orders.insert_one(o_data)
        await users.update_one({"user_id": uid}, {"$inc": {"credits": -amt}, "$set": {"step": None, "temp_data": None}})
        
        await m.reply(ORDER_SUCCESS.format(title=temp['title'], subs=subs, credits=amt))
        
        # Log Channel Alert
        try:
            await bot.send_message(LOG_CHANNEL, f"🆕 **New Order!**\n\n👤 User: `{uid}`\n📢 Channel: {temp['title']}\n👥 Subs: {subs}\n💰 Cost: {amt}")
        except: pass
