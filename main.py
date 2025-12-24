import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPrivileges
from pyrogram.errors import UserNotParticipant
from config import *
import database as db
from bson import ObjectId

app = Client("SubXBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ================= MENUS =================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Earn Credits", callback_data="earn"), InlineKeyboardButton("➕ Add Channel", callback_data="add")],
        [InlineKeyboardButton("📊 My Orders", callback_data="my_orders"), InlineKeyboardButton("💰 Balance", callback_data="bal")],
        [InlineKeyboardButton("🔗 Refer & Earn", callback_data="refer"), InlineKeyboardButton("💳 Buy", callback_data="buy")]
    ])

# ================= START & REFERRAL =================
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(_, m):
    user_id = m.from_user.id
    user_data = await db.get_user(user_id)
    
    # Referral Logic
    if len(m.command) > 1:
        ref_id = int(m.command[1])
        if ref_id != user_id and not user_data.get("referred_by"):
            await db.users.update_one({"user_id": user_id}, {"$set": {"referred_by": ref_id}})
            await db.add_credits(ref_id, REF_REWARD)
            try:
                await app.send_message(ref_id, f"🎊 **Referral Success!**\nUser {user_id} joined. You got +{REF_REWARD} credits.")
            except: pass

    await m.reply(f"👋 **Welcome to SubXChange!**\n\n💰 Balance: {user_data['credits']} Credits\n\nJoin channels to earn, or add yours to grow!", reply_markup=main_menu())

# ================= SMART LEAVE TRACKING =================
@app.on_chat_member_updated()
async def leave_monitor(_, update):
    if not update.new_chat_member and update.old_chat_member:
        user_id = update.old_chat_member.user.id
        chat_id = update.chat.id
        
        # Check if this channel has an active order
        order = await db.orders.find_one({"channel_id": chat_id, "status": "active"})
        if order:
            user = await db.get_user(user_id)
            if chat_id in user.get("joined_orders", []):
                # Penalty Logic
                await db.use_credits(user_id, PENALTY_CREDITS)
                await db.users.update_one({"user_id": user_id}, {"$pull": {"joined_orders": chat_id}})
                try:
                    await app.send_message(user_id, f"⚠️ **Penalty Alert!**\n\nAapne `{update.chat.title}` leave kiya jabki order active tha. **-{PENALTY_CREDITS} Credits** cut gaye.")
                except: pass

# ================= EARN SYSTEM =================
@app.on_callback_query(filters.regex("^earn$"))
async def earn_logic(_, cb):
    user = await db.get_user(cb.from_user.id)
    # Find active order user hasn't joined
    order = await db.orders.find_one({
        "status": "active",
        "user_id": {"$ne": cb.from_user.id},
        "channel_id": {"$nin": user.get("joined_orders", [])}
    })
    
    if not order:
        return await cb.answer("No channels available right now!", show_alert=True)
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=order['link'])],
        [InlineKeyboardButton("✅ Verify Join", callback_data=f"check_{order['_id']}")]
    ])
    await cb.message.edit_text(f"Join this channel to earn {JOIN_REWARD} credits:\n\n📌 **{order['title']}**", reply_markup=kb)

@app.on_callback_query(filters.regex("^check_"))
async def verify_join(_, cb):
    order_id = cb.data.split("_")[1]
    order = await db.orders.find_one({"_id": ObjectId(order_id)})
    
    try:
        member = await app.get_chat_member(order['channel_id'], cb.from_user.id)
        if member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            # Credit User
            await db.add_credits(cb.from_user.id, JOIN_REWARD)
            await db.users.update_one({"user_id": cb.from_user.id}, {"$push": {"joined_orders": order['channel_id']}})
            
            # Update Order
            new_done = order['completed'] + 1
            if new_done >= order['subscribers']:
                await db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": "completed", "completed": new_done}})
            else:
                await db.orders.update_one({"_id": ObjectId(order_id)}, {"$inc": {"completed": 1}})
            
            await cb.message.edit_text(f"✅ Verified! +{JOIN_REWARD} Credits added.", reply_markup=main_menu())
        else:
            await cb.answer("Join nahi kiya bhai!", show_alert=True)
    except UserNotParticipant:
        await cb.answer("Pehle join toh karo!", show_alert=True)
    except Exception as e:
        await cb.answer("Error: Bot is not admin in that channel anymore.")

# ================= ADD CHANNEL (Order) =================
@app.on_callback_query(filters.regex("^add$"))
async def add_start(_, cb):
    user = await db.get_user(cb.from_user.id)
    if user['credits'] < MIN_ORDER_CREDITS:
        return await cb.answer(f"Minimum {MIN_ORDER_CREDITS} credits chahiye!", show_alert=True)
    
    await cb.message.edit_text("Send your Channel Username (e.g., @MyChannel) or Private Chat ID.\n\n**Note:** Bot must be Admin in your channel!")

@app.on_message(filters.private & filters.text & ~filters.command("start"))
async def handle_channel_add(_, m):
    user = await db.get_user(m.from_user.id)
    if user['credits'] < MIN_ORDER_CREDITS: return

    try:
        chat = await app.get_chat(m.text)
        bot_member = await app.get_chat_member(chat.id, "me")
        if not bot_member.privileges: raise Exception("Not Admin")
        
        # Ask for Subs amount
        subs_needed = user['credits'] // JOIN_REWARD
        
        # Create Order
        new_order = {
            "user_id": m.from_user.id,
            "title": chat.title,
            "channel_id": chat.id,
            "link": f"https://t.me/{chat.username}" if chat.username else await app.export_chat_invite_link(chat.id),
            "subscribers": subs_needed,
            "completed": 0,
            "status": "active"
        }
        res = await db.orders.insert_one(new_order)
        await db.use_credits(m.from_user.id, user['credits'])
        
        # Log to Channel
        log_msg = f"🆕 **New Order!**\n\n📢 {chat.title}\n👥 Target: {subs_needed} Subs\n🆔 Order ID: `{res.inserted_id}`"
        await app.send_message(LOG_CHANNEL, log_msg)
        
        # Admin DM Alert
        for adm in ADMIN_IDS:
            await app.send_message(adm, f"🚀 Order Alert!\nUser: `{m.from_user.id}`\nChannel: {chat.title}")

        await m.reply(f"✅ Order Placed for {subs_needed} subscribers!")
    except Exception as e:
        await m.reply(f"❌ Error: Bot admin nahi hai ya channel galat hai. {e}")

# ================= RUN =================
if __name__ == "__main__":
    print("🤖 Bot Starting...")
    app.run()
