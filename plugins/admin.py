from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import is_admin, admins, users, orders
from config import ADMIN_IDS

# --- 1. ADMIN PANEL UI ---
async def get_admin_main_menu():
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
    if not await is_admin(m.from_user.id):
        return
    kb = await get_admin_main_menu()
    await m.reply("🛠 **Admin Control Panel**\n\nSare orders aur admins yahan se manage karein.", reply_markup=kb)

# --- 2. ADMIN LIST BUTTON ---
@Client.on_callback_query(filters.regex("^list_adm$"))
async def list_admins_callback(bot, cb):
    if not await is_admin(cb.from_user.id): return
    
    text = "📋 **Current Admins List:**\n\n"
    # Config Owners
    text += "👑 **Owners (Config):**\n"
    for owner in ADMIN_IDS:
        text += f"• `{owner}`\n"
    
    # DB Admins
    text += "\n👮 **Added Admins:**\n"
    found = False
    async for adm in admins.find({}):
        found = True
        text += f"• `{adm['user_id']}`\n"
    
    if not found:
        text += "_No additional admins added._"
    
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]]))

# --- 3. ADD/DEL ADMIN INSTRUCTIONS ---
@Client.on_callback_query(filters.regex("^(add_adm|del_adm)$"))
async def adm_actions_callback(bot, cb):
    if not await is_admin(cb.from_user.id): return
    
    if cb.data == "add_adm":
        text = "➕ **Add New Admin**\n\nNaya admin add karne ke liye niche wala command bhejien:\n\n`/add_admin [UserID]`"
    else:
        text = "🗑 **Delete Admin**\n\nAdmin hatane ke liye niche wala command bhejien:\n\n`/del_admin [UserID]`"
        
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]]))

# --- 4. ADD/DEL ADMIN COMMANDS (Super Admin Only) ---
@Client.on_message(filters.command("add_admin") & filters.private)
async def add_admin_logic(bot, m):
    # Sirf Config wale Owners hi naya admin bana sakte hain
    if m.from_user.id not in ADMIN_IDS:
        return await m.reply("❌ Sirf Super Admins (Owners) hi naye admin add kar sakte hain!")
    
    if len(m.command) < 2:
        return await m.reply("❌ Format galat hai!\nUse: `/add_admin 12345678` (User ID)")
    
    try:
        target_id = int(m.command[1])
        await admins.update_one({"user_id": target_id}, {"$set": {"user_id": target_id}}, upsert=True)
        await m.reply(f"✅ User `{target_id}` ko Admin list mein add kar diya gaya hai!")
    except ValueError:
        await m.reply("❌ User ID hamesha numbers mein hoti hai.")

@Client.on_message(filters.command("del_admin") & filters.private)
async def del_admin_logic(bot, m):
    if m.from_user.id not in ADMIN_IDS:
        return await m.reply("❌ Sirf Super Admins hi admin hata sakte hain!")
    
    if len(m.command) < 2:
        return await m.reply("❌ Format galat hai!\nUse: `/del_admin 12345678` (User ID)")
    
    try:
        target_id = int(m.command[1])
        result = await admins.delete_one({"user_id": target_id})
        if result.deleted_count > 0:
            await m.reply(f"🗑 User `{target_id}` ko Admin list se hata diya gaya.")
        else:
            await m.reply("❌ Ye ID admin list mein nahi mili.")
    except ValueError:
        await m.reply("❌ User ID numbers mein honi chahiye.")

# --- 5. BACK NAVIGATION ---
@Client.on_callback_query(filters.regex("^admin_back$"))
async def back_to_admin_panel(bot, cb):
    if not await is_admin(cb.from_user.id): return
    kb = await get_admin_main_menu()
    await cb.message.edit_text("🛠 **Admin Control Panel**", reply_markup=kb)
