from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import is_admin, admins, users, orders
from config import ADMIN_IDS

@Client.on_message(filters.command("admin") & filters.private)
async def admin_panel(bot, m):
    if not await is_admin(m.from_user.id): return
    
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📦 Ongoing Orders", callback_data="manage_active_0"),
            InlineKeyboardButton("✅ Completed Orders", callback_data="manage_history_0")
        ],
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        [
            InlineKeyboardButton("➕ Add Admin", callback_data="add_adm"),
            InlineKeyboardButton("📋 Admin List", callback_data="list_adm"),
            InlineKeyboardButton("🗑 Del Admin", callback_data="del_adm")
        ],
        [InlineKeyboardButton("⬅️ Back Menu", callback_data="home")]
    ])
    await m.reply("🛠 **Admin Control Panel**\nSare orders aur admins yahan se manage karein.", reply_markup=kb)

@Client.on_callback_query(filters.regex("^admin_stats$"))
async def admin_stats_h(bot, cb):
    if not await is_admin(cb.from_user.id): return
    u = await users.count_documents({})
    o = await orders.count_documents({})
    ao = await orders.count_documents({"status": "active"})
    text = f"📊 **Bot Stats**\n\n👤 Total Users: `{u}`\n📦 Total Orders: `{o}`\n🚀 Active Orders: `{ao}`"
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]]))

@Client.on_callback_query(filters.regex("^list_adm$"))
async def list_admins(bot, cb):
    if not await is_admin(cb.from_user.id): return
    text = "👮 **Admins List:**\n\n"
    async for adm in admins.find({}):
        text += f"• `{adm['user_id']}`\n"
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]]))

@Client.on_callback_query(filters.regex("^(add_adm|del_adm)$"))
async def adm_action_msg(bot, cb):
    if not await is_admin(cb.from_user.id): return
    cmd = "add_admin" if cb.data == "add_adm" else "del_admin"
    await cb.message.edit_text(f"Admin handle karne ke liye command use karein:\n\n`/{cmd} [UserID]`")

@Client.on_callback_query(filters.regex("^admin_back$"))
async def back_to_adm(bot, cb): await admin_panel(bot, cb.message)

# Commands for Owners to Manage Admins
@Client.on_message(filters.command("add_admin") & filters.user(ADMIN_IDS))
async def add_adm_cmd(bot, m):
    if len(m.command) < 2: return
    tid = int(m.command[1])
    await admins.update_one({"user_id": tid}, {"$set": {"user_id": tid}}, upsert=True)
    await m.reply(f"✅ User `{tid}` added as admin.")

@Client.on_message(filters.command("del_admin") & filters.user(ADMIN_IDS))
async def del_adm_cmd(bot, m):
    if len(m.command) < 2: return
    tid = int(m.command[1])
    await admins.delete_one({"user_id": tid})
    await m.reply(f"🗑 User `{tid}` removed from admin.")
