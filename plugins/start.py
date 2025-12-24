import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import get_user, users
from config import (
    START_MSG, HELP_MSG, ABOUT_MSG, START_IMG, 
    START_STICKER, REF_REWARD
)

# ================= START COMMAND =================

@Client.on_message(filters.command("start") & filters.private)
async def on_start(bot, m):
    uid = m.from_user.id
    u_data = await get_user(uid)
    
    # 1. --- STICKER LOGIC (Send & Auto-Delete) ---
    try:
        if START_STICKER:
            sticker_msg = await m.reply_sticker(START_STICKER)
            await asyncio.sleep(2) # 2 second wait
            await sticker_msg.delete()
    except Exception as e:
        print(f"Sticker Error: {e}")

    # 2. --- REFERRAL LOGIC ---
    if len(m.command) > 1 and m.command[1].isdigit():
        ref_id = int(m.command[1])
        # Check: Khud ko refer nahi kar raha aur pehle kisi ne refer nahi kiya
        if ref_id != uid and not u_data.get("referred_by"):
            await users.update_one({"user_id": uid}, {"$set": {"referred_by": ref_id}})
            await users.update_one({"user_id": ref_id}, {"$inc": {"credits": REF_REWARD}})
            try:
                await bot.send_message(
                    ref_id, 
                    f"🎊 **Referral Bonus!**\n\nEk naye dost ne join kiya. Aapko milenge **+{REF_REWARD} Credits!**"
                )
            except:
                pass

    # 3. --- MAIN MENU BUTTONS ---
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
    
    # 4. --- SEND MAIN PHOTO WITH CAPTION ---
    try:
        await m.reply_photo(
            photo=START_IMG,
            caption=START_MSG.format(bal=u_data.get('credits', 0), ref=REF_REWARD),
            reply_markup=kb
        )
    except Exception as e:
        # Agar photo ID/Link galat ho toh simple text bhej dega
        print(f"Photo Error: {e}")
        await m.reply_text(
            START_MSG.format(bal=u_data.get('credits', 0), ref=REF_REWARD),
            reply_markup=kb
        )

# ================= CALLBACK QUERIES (Help/About/Home) =================

@Client.on_callback_query(filters.regex("^(help|about|home)$"))
async def start_callbacks(bot, cb):
    uid = cb.from_user.id
    u_data = await get_user(uid)
    
    # Help Menu
    if cb.data == "help":
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back Menu", callback_data="home")]])
        await cb.message.edit_caption(caption=HELP_MSG, reply_markup=kb)
        
    # About Menu
    elif cb.data == "about":
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back Menu", callback_data="home")]])
        await cb.message.edit_caption(caption=ABOUT_MSG, reply_markup=kb)
        
    # Home Menu (Wapas Start Menu par aana)
    elif cb.data == "home":
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
        await cb.message.edit_caption(
            caption=START_MSG.format(bal=u_data.get('credits', 0), ref=REF_REWARD),
            reply_markup=kb
        )

# ================= REFER CALLBACK =================

@Client.on_callback_query(filters.regex("^refer$"))
async def refer_callback(bot, cb):
    bot_info = await bot.get_me()
    uid = cb.from_user.id
    
    # config.py se REFER_MSG uthayega
    from config import REFER_MSG
    
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back Menu", callback_data="home")]])
    
    await cb.message.edit_caption(
        caption=REFER_MSG.format(username=bot_info.username, uid=uid, reward=REF_REWARD),
        reply_markup=kb
    )
