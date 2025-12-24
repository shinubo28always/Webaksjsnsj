import asyncio
import re
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked
from db import users
from config import ADMIN_IDS

# --- Helper Function: Time Parser for tbroadcast ---
def parse_duration(duration_str):
    total_seconds = 0
    # Pattern to find hours and minutes (e.g., 01h, 44m, 01h44m)
    hours = re.search(r'(\d+)h', duration_str)
    minutes = re.search(r'(\d+)m', duration_str)
    
    if hours:
        total_seconds += int(hours.group(1)) * 3600
    if minutes:
        total_seconds += int(minutes.group(1)) * 60
    
    return total_seconds

# ================= 1. NORMAL BROADCAST =================
@Client.on_message(filters.command("broadcast") & filters.user(ADMIN_IDS))
async def normal_broadcast(bot, m):
    if not m.reply_to_message:
        return await m.reply("❌ Kisi message ko reply karke command do!")
    
    msg = await m.reply("🚚 **Normal Broadcast shuru ho raha hai...**")
    all_users = users.find({})
    count = 0
    blocked = 0
    
    async for user in all_users:
        try:
            await m.reply_to_message.copy(chat_id=user['user_id'])
            count += 1
            await asyncio.sleep(0.3) # Rate limit se bachne ke liye
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except (UserIsBlocked, InputUserDeactivated):
            blocked += 1
        except Exception:
            pass
            
    await msg.edit(f"✅ **Broadcast Complete!**\n\n👤 Sent to: {count}\n🚫 Blocked: {blocked}")

# ================= 2. PIN BROADCAST =================
@Client.on_message(filters.command("pbroadcast") & filters.user(ADMIN_IDS))
async def pin_broadcast(bot, m):
    if not m.reply_to_message:
        return await m.reply("❌ Message ko reply karke `/pbroadcast` likho!")
    
    msg = await m.reply("📌 **Pin Broadcast shuru ho raha hai...**")
    all_users = users.find({})
    count = 0
    
    async for user in all_users:
        try:
            sent_msg = await m.reply_to_message.copy(chat_id=user['user_id'])
            await bot.pin_chat_message(chat_id=user['user_id'], message_id=sent_msg.id, both_sides=True)
            count += 1
            await asyncio.sleep(0.5)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            pass
            
    await msg.edit(f"✅ **Pin Broadcast Complete!**\nSent & Pinned for {count} users.")

# ================= 3. TEMPORARY BROADCAST =================
@Client.on_message(filters.command("tbroadcast") & filters.user(ADMIN_IDS))
async def temp_broadcast(bot, m):
    if not m.reply_to_message:
        return await m.reply("❌ Message ko reply karke `/tbroadcast 01h30m` likho!")
    
    if len(m.command) < 2:
        return await m.reply("📝 **Format:** `/tbroadcast 01h30m` (Max 12h)")
    
    duration_str = m.command[1]
    seconds = parse_duration(duration_str)
    
    if seconds <= 0:
        return await m.reply("❌ Galat format! Use: `01h`, `10m`, ya `01h20m`")
    
    if seconds > 43200: # 12 Hours limit
        return await m.reply("⚠️ Max limit 12 hours hai!")

    msg = await m.reply(f"⏳ **Temp Broadcast shuru...**\nMessage {duration_str} baad delete ho jayega.")
    all_users = users.find({})
    
    sent_messages = [] # List to track messages for deletion

    async for user in all_users:
        try:
            sent = await m.reply_to_message.copy(chat_id=user['user_id'])
            sent_messages.append((user['user_id'], sent.id))
            await asyncio.sleep(0.3)
        except Exception:
            pass

    await msg.edit(f"🚀 **Broadcast Sent!**\nAb ye {duration_str} tak rahega.")
    
    # Wait for the duration
    await asyncio.sleep(seconds)
    
    # Delete messages
    for user_id, msg_id in sent_messages:
        try:
            await bot.delete_messages(chat_id=user_id, message_ids=msg_id)
        except:
            pass
            
    await m.reply(f"🗑 **Temp Broadcast Cleanup Complete!**\nSaare messages delete kar diye gaye.")
