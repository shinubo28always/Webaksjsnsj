import math
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import orders, users, is_admin
from config import JOIN_REWARD, LOG_CHANNEL
from bson import ObjectId

# --- Helper: Check Admin Authorization ---
async def check_admin(cb):
    if not await is_admin(cb.from_user.id):
        await cb.answer("❌ Aap Admin nahi hain!", show_alert=True)
        return False
    return True

# --- 1. LIST VIEW WITH PAGINATION (Active/History) ---
@Client.on_callback_query(filters.regex(r"^manage_(active|history)_(\d+)$"))
async def list_orders(bot, cb):
    if not await check_admin(cb): return
    
    o_type = cb.data.split("_")[1]
    page = int(cb.data.split("_")[2])
    status = "active" if o_type == "active" else "completed"
    
    limit = 5 # Ek page pe 5 orders dikhayega
    skip = page * limit
    
    total_orders = await orders.count_documents({"status": status})
    total_pages = math.ceil(total_orders / limit)
    
    if total_orders == 0:
        return await cb.message.edit_text(f"❌ Abhi koi {status} orders nahi hain.", 
                                         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_back")]]))

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
    
    buttons.append([InlineKeyboardButton("⬅️ Admin Menu", callback_data="admin_back")])
    
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# --- 2. SPECIFIC ORDER VIEW (Details & Actions) ---
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
    # Agar order chal raha hai toh cancel/refund ka option
    if o['status'] == "active":
        kb.append([InlineKeyboardButton("❌ Cancel & Partial Refund", callback_data=f"cancel_{oid}")])
    
    kb.append([InlineKeyboardButton("🗑 Force Delete", callback_data=f"fdelete_{oid}")])
    kb.append([InlineKeyboardButton("⬅️ Back to List", callback_data="manage_active_0")])
    
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb))

# --- 3. CANCEL & PARTIAL REFUND LOGIC ---
@Client.on_callback_query(filters.regex(r"^cancel_"))
async def cancel_order(bot, cb):
    if not await check_admin(cb): return
    
    oid = cb.data.split("_")[1]
    o = await orders.find_one({"_id": ObjectId(oid)})
    
    if not o or o['status'] != "active":
        return await cb.answer("Ye order ab cancel nahi ho sakta!")

    # Logic: Jitne subs bache hain unka refund
    remaining = o['subscribers'] - o['completed']
    refund = max(0, remaining * JOIN_REWARD)
    
    # 1. Update User Balance
    await users.update_one({"user_id": o['user_id']}, {"$inc": {"credits": refund}})
    
    # 2. Update Order Status
    await orders.update_one({"_id": ObjectId(oid)}, {"$set": {"status": "cancelled"}})
    
    # 3. Notification to Log Channel
    log_msg = (f"🛑 **Order Cancelled by Admin**\n\n"
               f"👤 User: `{o['user_id']}`\n"
               f"📢 Channel: {o['title']}\n"
               f"💰 Refund: {refund} Credits")
    try: await bot.send_message(LOG_CHANNEL, log_msg)
    except: pass
    
    # 4. User ko notice
    try:
        await bot.send_message(o['user_id'], f"⚠️ **Order Cancelled:** Aapka order `{o['title']}` admin ne cancel kar diya hai. **{refund} credits** refund kar diye gaye hain.")
    except: pass
    
    await cb.answer(f"✅ Order Cancelled! Refunded {refund} credits.", show_alert=True)
    # Wapas menu par bhej do
    await cb.message.edit_text("🔄 **Order Processed!**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Orders", callback_data="manage_active_0")]]))

# --- 4. FORCE DELETE (No Refund) ---
@Client.on_callback_query(filters.regex(r"^fdelete_"))
async def force_delete_order(bot, cb):
    if not await check_admin(cb): return
    
    oid = cb.data.split("_")[1]
    await orders.delete_one({"_id": ObjectId(oid)})
    
    await cb.answer("🗑 Order deleted permanently!", show_alert=True)
    await cb.message.edit_text("✅ Order removed from database.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Orders", callback_data="manage_active_0")]]))
