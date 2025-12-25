import math
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import orders, users, is_admin
from config import JOIN_REWARD, LOG_CHANNEL
from bson import ObjectId

# --- 1. MAIN ORDERS DASHBOARD FUNCTION ---
async def get_orders_menu(bot, uid):
    active_count = await orders.count_documents({"status": "active"})
    completed_count = await orders.count_documents({"status": "completed"})
    
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
    return "📂 **Orders Control Center**\n\nNiche diye gaye buttons se orders manage karein:", kb

@Client.on_message(filters.command("orders") & filters.private)
async def admin_orders_cmd(bot, m):
    if not await is_admin(m.from_user.id): return
    text, kb = await get_orders_menu(bot, m.from_user.id)
    await m.reply(text, reply_markup=kb)

# --- 2. NAVIGATION HANDLERS (Back Buttons Fix) ---
@Client.on_callback_query(filters.regex("^orders_home$"))
async def orders_home_nav(bot, cb):
    if not await is_admin(cb.from_user.id): return
    text, kb = await get_orders_menu(bot, cb.from_user.id)
    await cb.message.edit_text(text, reply_markup=kb)

# --- 3. PING & STATS ---
@Client.on_callback_query(filters.regex("^admin_ping$"))
async def ping_handler(bot, cb):
    if not await is_admin(cb.from_user.id): return
    start_time = time.time()
    await cb.answer("Pinging...")
    ping_ms = round((time.time() - start_time) * 1000, 2)
    await cb.message.edit_text(f"🚀 **Bot Latency:** `{ping_ms} ms`", 
                               reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="orders_home")]]))

@Client.on_callback_query(filters.regex("^admin_stats$"))
async def stats_handler(bot, cb):
    if not await is_admin(cb.from_user.id): return
    u, o, ao = await users.count_documents({}), await orders.count_documents({}), await orders.count_documents({"status": "active"})
    await cb.message.edit_text(f"📊 **Stats**\n\nUsers: `{u}`\nTotal Orders: `{o}`\nActive: `{ao}`", 
                               reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="orders_home")]]))

# --- 4. LIST VIEW & PAGINATION ---
@Client.on_callback_query(filters.regex(r"^manage_(active|history)_(\d+)$"))
async def list_orders(bot, cb):
    if not await is_admin(cb.from_user.id): return
    o_type, page = cb.data.split("_")[1], int(cb.data.split("_")[2])
    status = "active" if o_type == "active" else "completed"
    limit, skip = 5, page * 5
    total = await orders.count_documents({"status": status})
    total_pages = math.ceil(total / limit)

    if total == 0:
        return await cb.message.edit_text(f"❌ No {status} orders.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="orders_home")]]))

    cursor = orders.find({"status": status}).skip(skip).limit(limit)
    buttons = []
    async for o in cursor:
        buttons.append([InlineKeyboardButton(f"📢 {o['title']} ({o['completed']}/{o['subscribers']})", callback_data=f"view_{o['_id']}")])
    
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"manage_{o_type}_{page-1}"))
    if page < total_pages - 1: nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"manage_{o_type}_{page+1}"))
    if nav: buttons.append(nav)
    buttons.append([InlineKeyboardButton("⬅️ Orders Menu", callback_data="orders_home")])
    
    await cb.message.edit_text(f"📂 **{status.capitalize()} Orders (Page {page+1})**", reply_markup=InlineKeyboardMarkup(buttons))

# --- 5. VIEW & ACTIONS ---
@Client.on_callback_query(filters.regex(r"^view_"))
async def view_detail(bot, cb):
    if not await is_admin(cb.from_user.id): return
    o = await orders.find_one({"_id": ObjectId(cb.data.split("_")[1])})
    if not o: return await cb.answer("Order not found!")
    
    text = f"📑 **Order Info**\n\nChannel: {o['title']}\nSubs: `{o['completed']}/{o['subscribers']}`\nStatus: {o['status'].upper()}"
    kb = []
    if o['status'] == "active":
        kb.append([InlineKeyboardButton("❌ Cancel & Refund", callback_data=f"cancel_{o['_id']}")])
    kb.append([InlineKeyboardButton("🗑 Force Delete", callback_data=f"fdelete_{o['_id']}")])
    kb.append([InlineKeyboardButton("⬅️ Back", callback_data="manage_active_0")])
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

@Client.on_callback_query(filters.regex(r"^(cancel|fdelete)_"))
async def action_handler(bot, cb):
    if not await is_admin(cb.from_user.id): return
    action, oid = cb.data.split("_")
    o = await orders.find_one({"_id": ObjectId(oid)})
    if action == "cancel":
        refund = max(0, (o['subscribers'] - o['completed']) * JOIN_REWARD)
        await users.update_one({"user_id": o['user_id']}, {"$inc": {"credits": refund}})
        await orders.update_one({"_id": ObjectId(oid)}, {"$set": {"status": "cancelled"}})
        await cb.answer(f"Refunded {refund} credits!")
    else:
        await orders.delete_one({"_id": ObjectId(oid)})
        await cb.answer("Deleted!")
    await cb.message.edit_text("✅ Done!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="orders_home")]]))
