import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import get_user, users
from config import (
    START_MSG, HELP_MSG, ABOUT_MSG, START_IMG, 
    START_STICKER, REF_REWARD
)

@Client.on_message(filters.command("start") & filters.private)
async def on_start(bot, m):
    uid = m.from_user.id
    u_data = await get_user(uid)
    
    # 1. Send Sticker
    sticker_msg = await m.reply_sticker(START_STICKER)
    
    # 2. Wait for 2 seconds and Delete Sticker
    await asyncio.sleep(2)
    await sticker_msg.delete()
    
    # 3. Referral Logic (If any)
    if len(m.command) > 1 and m.command[1].isdigit():
        ref_id = int(m.command[1])
        if ref_id != uid and not u_data.get("referred_by"):
            await users.update_one({"user_id": uid}, {"$set": {"referred_by": ref_id}})
            await users.update_one({"user_id": ref_id}, {"$inc": {"credits": REF_REWARD}})
            try: await bot.send_message(ref_id, f"🎊 Referral Success! +{REF_REWARD} credits.")
            except: pass

    # 4. Buttons for Start Menu
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔥 Earn Credits", callback_data="earn"),
            InlineKeyboardButton("➕ Add Channel", callback_data="add")
        ],
        [
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
            InlineKeyboardButton("🤖 About", callback_data="about")
        ],
        [InlineKeyboardButton("🔗 Refer & Earn", callback_data="refer")]
    ])
    
    # 5. Send Photo with Caption
    await m.reply_photo(
        photo=START_IMG,
        caption=START_MSG.format(bal=u_data['credits'], ref=REF_REWARD),
        reply_markup=kb
    )

# --- Help & About Callbacks ---

@Client.on_callback_query(filters.regex("^(help|about|home)$"))
async def start_callbacks(bot, cb):
    uid = cb.from_user.id
    u_data = await get_user(uid)
    
    if cb.data == "help":
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="home")]])
        await cb.message.edit_caption(HELP_MSG, reply_markup=kb)
        
    elif cb.data == "about":
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="home")]])
        await cb.message.edit_caption(ABOUT_MSG, reply_markup=kb)
        
    elif cb.data == "home":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 Earn", callback_data="earn"), InlineKeyboardButton("➕ Add", callback_data="add")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help"), InlineKeyboardButton("🤖 About", callback_data="about")],
            [InlineKeyboardButton("🔗 Refer", callback_data="refer")]
        ])
        await cb.message.edit_caption(
            START_MSG.format(bal=u_data['credits'], ref=REF_REWARD), 
            reply_markup=kb
                                                      )
