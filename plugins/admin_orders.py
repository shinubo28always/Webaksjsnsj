import math
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import orders, users, is_admin
from config import JOIN_REWARD, LOG_CHANNEL
from bson import ObjectId

# --- 1. MAIN ORDERS COMMAND ---
@Client.on_message(filters.command("orders") & filters.private)
async def admin_orders_dashboard(bot, m):
    # Check if user is admin
    if not await is_admin(m.from_user.id):
        return

    # Counting for buttons
    active_count = await orders.count_documents({"status": "active"})
    completed_count = await orders.count_documents({"status": "completed"})
    
    # ROW 1: Ongoing | Completed
    # ROW 2: Ping | Stats
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"📦 Ongoing ({active_count})", callback_data="manage_active_0"),
            InlineKeyboardButton(f"✅ Completed ({completed_count})", callback_data="manage_history_0")
        ],
        [
            InlineKeyboardButton("📌 Ping", callback_data="admin_ping"),
            InlineKeyboardButton("📊 Stats", callback_data="admin_stats")
        ],
        [InlineKeyboardButton("⬅️ Back to Admin Panel", callback_data="admin_back")]
    ])
    
    await m.reply(
        "📂 **Orders Control Center**\n\nNiche diye gaye buttons se orders manage karein ya bot ki performance check karein.", 
        reply_markup=kb
    )

# --- 2. PING LOGIC (Response Time) ---
@Client.on_callback_query(filters.regex("^admin_ping$"))
async def ping_handler(bot, cb):
    if not await is_admin(cb.from_user.id): return
    
    start_time = time.time()
    await cb.answer("Pinging...", show_alert=False)
    end_time = time.time()
    
    ping_ms = round((end_time - start_time) * 1000, 2)
    
    await cb.message.edit_text(
        f"🚀 **Bot Latency (Ping)**\n\n📶 Speed: `{ping_ms} ms`\n🛰 Server: Online\n\nBot ekdam fast respond kar raha hai!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="orders_home")]])
    )

# --- 3. STATS LOGIC ---
@Client.on_callback_query(filters.regex("^admin_stats$"))
async def stats_handler(bot, cb):
    if not await is_admin(cb.from_user.id): return
    
    u_count = await users.count_documents({})
    o_total = await orders.count_documents({})
    o_active = await orders.count_documents({"status": "active"})
    
    text = (f"📊 **Live Statistics**\n\n"
            f"👤 Total Users: `{u_count}`\n"
            f"📦 Total Orders: `{o_total}`\n"
            f"🚀 Active Orders: `{o_active}`\n"
            f"💰 Admin Balance: Unlimited")
    
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="orders_home")]]))

# --- 4. LIST VIEW WITH PAGINATION (Ongoing/Completed) ---
@Client.on_callback_query(filters.regex(r"^manage_(active|history)_(\d+)$"))
async def list_orders(bot, cb):
    if not await is_admin(cb.from_user.id): return
    
    o_type = cb.data.split("_")[1]
    page = int(cb.data.split("_")[2])
    status = "active" if o_type == "active" else "completed"
    
    limit = 5 
    skip = page * limit
    
    total_orders = await orders.count_documents({"status": status})
    total_pages = math.ceil(total_orders / limit)
    
    if total_orders == 0:
        return await cb.message.edit_text(f"❌ Abhi koi {status} orders nahi hain.", 
                                         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="orders_home")]]))

    cursor = orders.find({"status": status}).skip(skip).limit(limit)
    
    text = f"📂 **Manage {status.capitalize()} Orders**\nPage: `{page+1}/{total_pages}`"
    buttons = []
    
    async for o in cursor:
        buttons.append([InlineKeyboardButton(f"📢 {o['title']} ({o['completed']}/{o['subscribers']})", callback_data=f"view_{o['_id']}")])
    
    nav_btns = []
    if page > 0:
        nav_btns.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"manage_{o_type}_{page-1}"))
    if page < total_pages - 1:
        nav_btns.append(InlineKeyboardButton("Next ➡️", callback_data=f"manage_{o_type}_{page+1}"))
    
    if nav_btns: buttons.append(nav_btns)
    buttons.append([InlineKeyboardButton("⬅️ Orders Menu", callback_data="orders_home")])
    
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# --- 5. ORDER DETAILS & CANCEL/REFUND ---
@Client.on_callback_query(filters.regex(r"^view_"))
async def view_detail(bot, cb):
    if not await is_admin(cb.from_user.id): return
    oid = cb.data.split("_")[1]
    o = await orders.find_one({"_id": ObjectId(oid)})
    
    if not o: return await cb.answer("Order not found!")
    
    text = (f"📑 **Order Info**\n\n"
            f"📢 Channel: {o['title']}\n"
            f"👥 Target: `{o['completed']}/{o['subscribers']}`\n"
            f"🆔 ID: `{o['_id']}`\n"
            f"🚦 Status: {o['status'].upper()}")
    
    kb = []
    if o['status'] == "active":
        kb.append([InlineKeyboardButton("❌ Cancel & Refund", callback_data=f"cancel_{oid}")])
    kb.append([InlineKeyboardButton("🗑 Force Delete", callback_data=f"fdelete_{oid}")])
    kb.append([InlineKeyboardButton("⬅️ Back", callback_data="manage_active_0")])
    
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

# --- 6. REFUND & DELETE LOGIC ---
@Client.on_callback_query(filters.regex(r"^(cancel|fdelete)_"))
async def action_handler(bot, cb):
    if not await is_admin(cb.from_user.id): return
    action, oid = cb.data.split("_")
    o = await orders.find_one({"_id": ObjectId(oid)})
    
    if action == "cancel":
        remaining = o['subscribers'] - o['completed']
        refund = max(0, remaining * JOIN_REWARD)
        await users.update_one({"user_id": o['user_id']}, {"$inc": {"credits": refund}})
        await orders.update_one({"_id": ObjectId(oid)}, {"$set": {"status": "cancelled"}})
        await cb.answer(f"Refunded {refund} credits!", show_alert=True)
    else:
        await orders.delete_one({"_id": ObjectId(oid)})
        await cb.answer("Order Deleted!", show_alert=True)
        
    await cb.message.edit_text("✅ Task Completed!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="orders_home")]]))

# --- NAVIGATION HELPER ---
@Client.on_callback_query(filters.regex("^orders_home$"))
async def home_nav(bot, cb):
    await admin_orders_dashboard(bot, cb.message)

@Client.on_callback_query(filters.regex("^admin_back$"))
async def back_to_main_panel(bot, cb):
    # Import locally to avoid circular import
    from plugins.admin import admin_panel
    await admin_panel(bot, cb.message)
