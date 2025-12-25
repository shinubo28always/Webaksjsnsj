import math
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import orders, users, is_admin
from config import JOIN_REWARD, LOG_CHANNEL
from bson import ObjectId

# --- 1. COMMAND HANDLER (/orders) ---
# Ye command ab kaam karegi
@Client.on_message(filters.command("orders") & filters.private)
async def admin_orders_cmd(bot, m):
    # Check if user is admin
    if not await is_admin(m.from_user.id):
        return

    active_count = await orders.count_documents({"status": "active"})
    completed_count = await orders.count_documents({"status": "completed"})
    
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"🚀 Active ({active_count})", callback_data="manage_active_0"),
            InlineKeyboardButton(f"✅ History ({completed_count})", callback_data="manage_history_0")
        ],
        [InlineKeyboardButton("⬅️ Back Menu", callback_data="home")]
    ])
    
    await m.reply("📂 **Orders Management**\n\nNiche diye gaye buttons se orders manage karein:", reply_markup=kb)


# --- Helper: Check Admin Authorization for Callbacks ---
async def check_admin(cb):
    if not await is_admin(cb.from_user.id):
        await cb.answer("❌ Aap Admin nahi hain!", show_alert=True)
        return False
    return True

# --- 2. LIST VIEW WITH PAGINATION (Active/History) ---
@Client.on_callback_query(filters.regex(r"^manage_(active|history)_(\d+)$"))
async def list_orders(bot, cb):
    if not await check_admin(cb): return
    
    o_type = cb.data.split("_")[1]
    page = int(cb.data.split("_")[2])
    status = "active" if o_type == "active" else "completed"
    
    limit = 5 
    skip = page * limit
    
    total_orders = await orders.count_documents({"status": status})
    total_pages = math.ceil(total_orders / limit)
    
    if total_orders == 0:
        return await cb.message.edit_text(f"❌ Abhi koi {status} orders nahi hain.", 
                                         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_home")]]))

    cursor = orders.find({"status": status}).skip(skip).limit(limit)
    
    text = f"📂 **Manage {status.capitalize()} Orders**\nPage: `{page+1}/{total_pages}`\n\nOrder manage karne ke liye niche click karein:"
    buttons = []
    
    async for o in cursor:
        buttons.append([InlineKeyboardButton(f"📢 {o['title']} ({o['completed']}/{o['subscribers']})", callback_data=f"view_{o['_id']}")])
    
    # Pagination Buttons
    nav_btns = []
    if page > 0:
        nav_btns.append(InlineKeyboardButton("⬅️ Back", callback_data=f"manage_{o_type}_{page-1}"))
    if page < total_pages - 1:
        nav_btns.append(InlineKeyboardButton("Next ➡️", callback_data=f"manage_{o_type}_{page+1}"))
    
    if nav_btns:
        buttons.append(nav_btns)
    
    buttons.append([InlineKeyboardButton("⬅️ Admin Menu", callback_data="admin_home")])
    
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# --- 3. SPECIFIC ORDER VIEW (Details & Actions) ---
@Client.on_callback_query(filters.regex(r"^view_"))
async def view_order_detail(bot, cb):
    if not await check_admin(cb): return
    
    oid = cb.data.split("_")[1]
    o = await orders.find_one({"_id": ObjectId(oid)})
    
    if not o:
        return await cb.answer("Order nahi mila!", show_alert=True)
    
    text = (f"📑 **Order Details**\n\n"
            f"📢 **Channel:** {o['title']}\n"
            f"👤 **Owner:** `{o['user_id']}`\n"
            f"👥 **Progress:** `{o['completed']}/{o['subscribers']}`\n"
            f"💰 **Total Cost:** {o['subscribers'] * JOIN_REWARD} Credits\n"
            f"🚦 **Status:** {o['status'].upper()}\n"
            f"🆔 **ID:** `{o['_id']}`")
    
    kb = []
    if o['status'] == "active":
        kb.append([InlineKeyboardButton("❌ Cancel & Partial Refund", callback_data=f"cancel_{oid}")])
    
    kb.append([InlineKeyboardButton("🗑 Force Delete", callback_data=f"fdelete_{oid}")])
    kb.append([InlineKeyboardButton("⬅️ Back to List", callback_data="manage_active_0")])
    
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

# --- 4. CANCEL & PARTIAL REFUND LOGIC ---
@Client.on_callback_query(filters.regex(r"^cancel_"))
async def cancel_order(bot, cb):
    if not await check_admin(cb): return
    
    oid = cb.data.split("_")[1]
    o = await orders.find_one({"_id": ObjectId(oid)})
    
    if not o or o['status'] != "active":
        return await cb.answer("Order cancel nahi ho sakta!")

    remaining = o['subscribers'] - o['completed']
    refund = max(0, remaining * JOIN_REWARD)
    
    await users.update_one({"user_id": o['user_id']}, {"$inc": {"credits": refund}})
    await orders.update_one({"_id": ObjectId(oid)}, {"$set": {"status": "cancelled"}})
    
    try: await bot.send_message(LOG_CHANNEL, f"🛑 **Order Cancelled**\nChannel: {o['title']}\nRefund: {refund}")
    except: pass
    
    try: await bot.send_message(o['user_id'], f"⚠️ Aapka order `{o['title']}` cancel kar diya gaya hai. {refund} credits wapas mil gaye hain.")
    except: pass
    
    await cb.answer(f"✅ Refunded {refund} credits.", show_alert=True)
    await cb.message.edit_text("🔄 Processed!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="manage_active_0")]]))

# --- 5. FORCE DELETE ---
@Client.on_callback_query(filters.regex(r"^fdelete_"))
async def force_delete_order(bot, cb):
    if not await check_admin(cb): return
    oid = cb.data.split("_")[1]
    await orders.delete_one({"_id": ObjectId(oid)})
    await cb.answer("🗑 Deleted!", show_alert=True)
    await cb.message.edit_text("✅ Removed.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="manage_active_0")]]))

# Helper for Admin Home (redirects to /admin panel view)
@Client.on_callback_query(filters.regex("^admin_home$"))
async def back_to_dash(bot, cb):
    # This button logic should exist in admin.py to show the full panel
    from plugins.admin import admin_panel
    await admin_panel(bot, cb.message)
