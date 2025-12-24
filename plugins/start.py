from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import get_user, users
from config import START_MSG, REF_REWARD

@Client.on_message(filters.command("start") & filters.private)
async def on_start(bot, m):
    uid = m.from_user.id
    u_data = await get_user(uid)
    
    # Referral
    if len(m.command) > 1 and m.command[1].isdigit():
        ref_id = int(m.command[1])
        if ref_id != uid and not u_data.get("referred_by"):
            await users.update_one({"user_id": uid}, {"$set": {"referred_by": ref_id}})
            await users.update_one({"user_id": ref_id}, {"$inc": {"credits": REF_REWARD}})
            try: await bot.send_message(ref_id, f"🎊 Referral Success! +{REF_REWARD} credits.")
            except: pass

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Earn", callback_data="earn"), InlineKeyboardButton("➕ Add", callback_data="add")],
        [InlineKeyboardButton("🔗 Refer", callback_data="refer")]
    ])
    
    await m.reply(START_MSG.format(bal=u_data['credits']), reply_markup=kb)
