import asyncio
import re
from pyrogram import Client, filters
from db import users, is_admin
from config import ADMIN_IDS

def parse_duration(duration_str):
    total_seconds = 0
    hours = re.search(r'(\d+)h', duration_str)
    minutes = re.search(r'(\d+)m', duration_str)
    if hours: total_seconds += int(hours.group(1)) * 3600
    if minutes: total_seconds += int(minutes.group(1)) * 60
    return total_seconds

@Client.on_message(filters.command("broadcast"))
async def normal_bc(bot, m):
    if not await is_admin(m.from_user.id): return
    if not m.reply_to_message: return await m.reply("Reply to a message!")
    msg = await m.reply("🚚 Normal Broadcast...")
    count = 0
    async for user in users.find({}):
        try:
            await m.reply_to_message.copy(user['user_id'])
            count += 1
            await asyncio.sleep(0.3)
        except: pass
    await msg.edit(f"✅ Sent to {count} users.")

@Client.on_message(filters.command("pbroadcast"))
async def pin_bc(bot, m):
    if not await is_admin(m.from_user.id): return
    if not m.reply_to_message: return await m.reply("Reply to a message!")
    msg = await m.reply("📌 Pin Broadcast...")
    count = 0
    async for user in users.find({}):
        try:
            sent = await m.reply_to_message.copy(user['user_id'])
            await bot.pin_chat_message(user['user_id'], sent.id, both_sides=True)
            count += 1
            await asyncio.sleep(0.5)
        except: pass
    await msg.edit(f"✅ Sent & Pinned for {count} users.")

@Client.on_message(filters.command("tbroadcast"))
async def temp_bc(bot, m):
    if not await is_admin(m.from_user.id): return
    if not m.reply_to_message or len(m.command) < 2:
        return await m.reply("Format: `/tbroadcast 01h30m` (Reply to message)")
    
    seconds = parse_duration(m.command[1])
    if seconds <= 0 or seconds > 43200: return await m.reply("Max 12h allowed!")
    
    msg = await m.reply(f"⏳ Temp Broadcast Sent for {m.command[1]}...")
    sent_msgs = []
    async for user in users.find({}):
        try:
            sent = await m.reply_to_message.copy(user['user_id'])
            sent_msgs.append((user['user_id'], sent.id))
            await asyncio.sleep(0.3)
        except: pass
    
    await asyncio.sleep(seconds)
    for u_id, m_id in sent_msgs:
        try: await bot.delete_messages(u_id, m_id)
        except: pass
    await m.reply("🗑 Temp Broadcast Cleanup Done!")
