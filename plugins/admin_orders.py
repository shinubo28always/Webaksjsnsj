from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import orders, users
from config import ADMIN_IDS, JOIN_REWARD, LOG_CHANNEL
from bson import ObjectId
import math

# --- 1. ADMIN ORDERS DASHBOARD ---
@Client.on_message(filters.command("orders") & filters.user(ADMIN_IDS))
async def admin_orders_dashboard(bot, m):
    active_count = await orders.count_documents({"status": "active"})
    completed_count = await orders.count_documents({"status": "completed"})
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🚀 Active Orders ({active_count})", callback_data="manage_active_0")],
        [InlineKeyboardButton(f"✅ Order History ({completed_count})", callback_data="manage_history_0")],
        [InlineKeyboardButton("❌ Close Menu", callback_data="close_admin")]
    ])
    
    await m.reply("📂 **Orders Management Panel**\n\nYahan se aap saare orders monitor aur control kar sakte hain.", reply_markup=kb)

# --- 2. LIST VIEW WITH PAGINATION (Active/History) ---
@Client.on_callback_query(filters.regex(r"^manage_(active|history)_(\d+)$") & filters.user(ADMIN_IDS))
async def list_orders(bot, cb):
    o_type = cb.data.split("_")[1]
    page = int(cb.data.split("_")[2])
    status = "active" if o_type == "active" else "completed"
    
    limit = 5 # Ek page pe 5 orders
    skip = page * limit
    
    total_orders = await orders.count_documents({"status": status})
    total_pages = math.ceil(total_orders / limit)
    
    cursor = orders.find({"status": status}).skip(skip).limit(limit)
    
    text = f"📂 **Manage {status.capitalize()} Orders (Page {page+1}/{total_pages})**\n\nKisi order ko manage karne ke liye niche button pe click karein:"
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
    
    buttons.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="admin_home")])
    
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# --- 3. SPECIFIC ORDER VIEW (Details & Actions) ---
@Client.on_callback_query(filters.regex(r"^view_") & filters.user(ADMIN_IDS))
async def view_order_detail(bot, cb):
    oid = cb.data.split("_")[1]
    o = await orders.find_one({"_id": ObjectId(oid)})
    
    if not o:
        return await cb.answer("Order nahi mila!", show_alert=True)
    
    text = (f"📑 **Order Details**\n\n"
            f"📢 **Channel:** {o['title']}\n"
            f"👤 **Owner ID:** `{o['user_id']}`\n"
            f"👥 **Progress:** `{o['completed']}/{o['subscribers']}`\n"
            f"💰 **Total Credits:** {o['subscribers'] * JOIN_REWARD}\n"
            f"🚦 **Status:** {o['status'].upper()}\n"
            f"🆔 **ID:** `{o['_id']}`")
    
    kb = []
    if o['status'] == "active":
        kb.append([InlineKeyboardButton("❌ Cancel & Partial Refund", callback_data=f"cancel_{oid}")])
    
    kb.append([InlineKeyboardButton("🗑 Force Delete", callback_data=f"fdelete_{oid}")])
    kb.append([InlineKeyboardButton("⬅️ Back to List", callback_data="manage_active_0")])
    
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

# --- 4. CANCEL & PARTIAL REFUND LOGIC ---
@Client.on_callback_query(filters.regex(r"^cancel_") & filters.user(ADMIN_IDS))
async def cancel_order(bot, cb):
    oid = cb.data.split("_")[1]
    o = await orders.find_one({"_id": ObjectId(oid)})
    
    if not o or o['status'] != "active":
        return await cb.answer("Order cancel nahi kiya ja sakta!")

    # Logic: Partial Refund
    remaining_subs = o['subscribers'] - o['completed']
    refund_amount = max(0, remaining_subs * JOIN_REWARD)
    
    # 1. Update User Balance
    await users.update_one({"user_id": o['user_id']}, {"$inc": {"credits": refund_amount}})
    
    # 2. Update Order Status
    await orders.update_one({"_id": ObjectId(oid)}, {"$set": {"status": "cancelled"}})
    
    # 3. Notification to Log Channel
    log_text = (f"❌ **Order Cancelled by Admin**\n\n"
                f"👤 User: `{o['user_id']}`\n"
                f"📢 Channel: {o['title']}\n"
                f"💰 Refunded: {refund_amount} Credits\n"
                f"👥 Completed: {o['completed']}/{o['subscribers']}")
    
    await bot.send_message(LOG_CHANNEL, log_text)
    
    # 4. Notification to User
    try:
        await bot.send_message(o['user_id'], f"⚠️ **Order Update:** Aapka order `{o['title']}` admin ne cancel kar diya hai. {refund_amount} credits aapke account me wapas bhej diye gaye hain.")
    except: pass
    
    await cb.answer("✅ Order Cancelled & Credits Refunded!", show_alert=True)
    await admin_orders_dashboard(bot, cb.message)

# --- 5. FORCE DELETE (Bina Refund) ---
@Client.on_callback_query(filters.regex(r"^fdelete_") & filters.user(ADMIN_IDS))
async def force_delete_order(bot, cb):
    oid = cb.data.split("_")[1]
    await orders.delete_one({"_id": ObjectId(oid)})
    await cb.answer("🗑 Order deleted permanently from database!", show_alert=True)
    await admin_orders_dashboard(bot, cb.message)

# Helper Callback for Main Menu
@Client.on_callback_query(filters.regex("^admin_home$"))
async def back_to_dash(bot, cb):
    await admin_orders_dashboard(bot, cb.message)

@Client.on_callback_query(filters.regex("^close_admin$"))
async def close_adm_panel(bot, cb):
    await cb.message.delete()
