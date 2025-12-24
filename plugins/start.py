import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import get_user, users
from config import *

@Client.on_message(filters.command("start") & filters.private)
async def on_start(bot, m):
    uid = m.from_user.id
    u_data = await get_user(uid)
    
    # 1. Sticker Animation
    try:
        if START_STICKER:
            stk = await m.reply_sticker(START_STICKER)
            await asyncio.sleep(2)
            await stk.delete()
    except: pass

    # 2. Referral logic
    if len(m.command) > 1 and m.command[1].isdigit():
        ref_id = int(m.command[1])
        if ref_id != uid and not u_data.get("referred_by"):
            await users.update_one({"user_id": uid}, {"$set": {"referred_by": ref_id}})
            await users.update_one({"user_id": ref_id}, {"$inc": {"credits": REF_REWARD}})
            try: await bot.send_message(ref_id, f"🎊 Referral Success! +{REF_REWARD} credits.")
            except: pass

    # 3. UI Menu
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Earn Credits", callback_data="earn"), InlineKeyboardButton("➕ Add Channel", callback_data="add")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help"), InlineKeyboardButton("🤖 About", callback_data="about")],
        [InlineKeyboardButton("🔗 Refer & Earn", callback_data="refer")]
    ])
    
    await m.reply_photo(
        photo=START_IMG, 
        caption=START_MSG.format(bal=u_data.get('credits', 0), ref=REF_REWARD), 
        reply_markup=kb
    )

@Client.on_callback_query(filters.regex("^(help|about|home)$"))
async def start_callbacks(bot, cb):
    uid = cb.from_user.id
    u_data = await get_user(uid)
    if cb.data == "help":
        await cb.message.edit_caption(HELP_MSG, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back Menu", callback_data="home")]]))
    elif cb.data == "about":
        await cb.message.edit_caption(ABOUT_MSG, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back Menu", callback_data="home")]]))
    elif cb.data == "home":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Earn", callback_data="earn"), InlineKeyboardButton("➕ Add", callback_data="add")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help"), InlineKeyboardButton("🤖 About", callback_data="about")],
            [InlineKeyboardButton("🔗 Refer", callback_data="refer")]
        ])
        await cb.message.edit_caption(START_MSG.format(bal=u_data.get('credits', 0), ref=REF_REWARD), reply_markup=kb)

@Client.on_callback_query(filters.regex("^refer$"))
async def refer_cb(bot, cb):
    me = await bot.get_me()
    await cb.message.edit_caption(
        REFER_MSG.format(username=me.username, uid=cb.from_user.id, reward=REF_REWARD), 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back Menu", callback_data="home")]])
                                                      )
