from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import is_admin, admins, users, orders
from config import ADMIN_IDS

# --- ADMIN PANEL UI FUNCTION ---
async def get_admin_panel_kb():
    return InlineKeyboardMarkup([
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
        [InlineKeyboardButton("⬅️ Back to Start", callback_data="home")]
    ])

@Client.on_message(filters.command("admin") & filters.private)
async def admin_panel_cmd(bot, m):
    if not await is_admin(m.from_user.id): return
    kb = await get_admin_panel_kb()
    await m.reply("🛠 **Admin Control Panel**", reply_markup=kb)

# --- BACK TO ADMIN PANEL HANDLER ---
@Client.on_callback_query(filters.regex("^admin_back$"))
async def admin_back_callback(bot, cb):
    if not await is_admin(cb.from_user.id): return
    kb = await get_admin_panel_kb()
    await cb.message.edit_text("🛠 **Admin Control Panel**", reply_markup=kb)

# ... (Add/Del Admin commands same rahengi) ...

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
