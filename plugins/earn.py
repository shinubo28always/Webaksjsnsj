from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from db import users, orders, get_user
from config import JOIN_REWARD, EARN_MSG, NOT_JOINED_MSG
from bson import ObjectId

# ================= 1. EARN BUTTON HANDLER =================
# Ye user ko wo channels dikhayega jo usne abhi tak join nahi kiye hain

@Client.on_callback_query(filters.regex("^earn$"))
async def earn_handler(bot, cb):
    uid = cb.from_user.id
    user = await get_user(uid)
    
    # Logic: Aisa order dhundo jo:
    # - Active ho
    # - Jiska owner ye khud user na ho
    # - Jise is user ne pehle kabhi join na kiya ho (anti-duplicate)
    order = await orders.find_one({
        "status": "active",
        "user_id": {"$ne": uid},
        "channel_id": {"$nin": user.get("joined_orders", [])}
    })
    
    if not order:
        return await cb.answer("😔 Abhi koi naya channel available nahi hai! Kuch der baad check karein.", show_alert=True)
    
    # Buttons for joining and verifying
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=order['link'])],
        [
            InlineKeyboardButton("✅ Verify Join", callback_data=f"verify_{order['_id']}"),
            InlineKeyboardButton("➡️ Skip", callback_data="earn")
        ],
        [InlineKeyboardButton("⬅️ Back Menu", callback_data="home")]
    ])
    
    # EARN_MSG config.py se format hoga
    await cb.message.edit_text(
        EARN_MSG.format(reward=JOIN_REWARD, title=order['title']),
        reply_markup=kb
    )

# ================= 2. VERIFY JOIN HANDLER =================
# Ye check karega ki user ne sach me join kiya ya nahi

@Client.on_callback_query(filters.regex("^verify_"))
async def verify_handler(bot, cb):
    uid = cb.from_user.id
    order_id = cb.data.split("_")[1]
    
    # Order details fetch karo
    order = await orders.find_one({"_id": ObjectId(order_id)})
    
    if not order or order['status'] != "active":
        return await cb.answer("❌ Ye order ab active nahi hai ya expire ho gaya!", show_alert=True)

    try:
        # Check Chat Member Status
        member = await bot.get_chat_member(order['channel_id'], uid)
        
        # Agar user member, admin ya owner hai
        if member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            
            # --- PEHLE CHECK: Kahin user ne pehle hi credit toh nahi liya? ---
            user = await get_user(uid)
            if order['channel_id'] in user.get("joined_orders", []):
                return await cb.answer("⚠️ Aap is channel ka credit pehle hi le chuke hain!", show_alert=True)

            # 1. User ko reward do aur channel ID 'joined_orders' list me dalo
            await users.update_one({"user_id": uid}, {
                "$inc": {"credits": JOIN_REWARD},
                "$push": {"joined_orders": order['channel_id']}
            })
            
            # 2. Order ki progress badhao
            new_done = order['completed'] + 1
            
            # 3. Check Order Completion
            if new_done >= order['subscribers']:
                # Order complete ho gaya
                await orders.update_one({"_id": ObjectId(order_id)}, {
                    "$set": {"status": "completed", "completed": new_done}
                })
                # Order owner ko notification bhejo
                try:
                    await bot.send_message(
                        order['user_id'], 
                        f"🎊 **Order Completed!**\n\nAapka order `{order['title']}` poora ho gaya hai. Saare subscribers mil chuke hain! ✅"
                    )
                except: pass
            else:
                # Order abhi chal raha hai
                await orders.update_one({"_id": ObjectId(order_id)}, {
                    "$inc": {"completed": 1}
                })
            
            # Success Message with Next Channel option
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Next Channel ➡️", callback_data="earn")],
                [InlineKeyboardButton("⬅️ Back Menu", callback_data="home")]
            ])
            
            await cb.message.edit_text(
                f"✅ **Verification Success!**\n\nAapko **+{JOIN_REWARD} Credits** de diye gaye hain.\n\nNext channel join karke aur kamaein! 👇",
                reply_markup=kb
            )
            
        else:
            # User chat me nahi hai
            await cb.answer(NOT_JOINED_MSG, show_alert=True)

    except UserNotParticipant:
        # User ne join nahi kiya error
        await cb.answer(NOT_JOINED_MSG, show_alert=True)
        
    except Exception as e:
        # Koi aur error (Bot admin nahi hai ya private chat access nahi hai)
        print(f"Verify Error: {e}")
        await cb.answer("❌ Error: Bot is channel me admin nahi hai! Admin se contact karein.", show_alert=True)
