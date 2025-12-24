from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from db import users, orders, get_user
from config import JOIN_REWARD, EARN_MSG, NOT_JOINED_MSG
from bson import ObjectId

@Client.on_callback_query(filters.regex("^earn$"))
async def earn_handler(bot, cb):
    uid = cb.from_user.id
    user = await get_user(uid)
    
    # Aisa order dhundo jo active ho aur user ne join na kiya ho
    order = await orders.find_one({
        "status": "active",
        "user_id": {"$ne": uid},
        "channel_id": {"$nin": user.get("joined_orders", [])}
    })
    
    if not order:
        return await cb.answer("Abhi koi channels available nahi hain! Baad me try karein.", show_alert=True)
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=order['link'])],
        [InlineKeyboardButton("✅ Verify Join", callback_data=f"verify_{order['_id']}")]
    ])
    
    await cb.message.edit_text(
        EAR_MSG.format(reward=JOIN_REWARD, title=order['title']),
        reply_markup=kb
    )

@Client.on_callback_query(filters.regex("^verify_"))
async def verify_handler(bot, cb):
    order_id = cb.data.split("_")[1]
    uid = cb.from_user.id
    order = await orders.find_one({"_id": ObjectId(order_id)})
    
    if not order:
        return await cb.answer("Ye order expire ho chuka hai!", show_alert=True)

    try:
        member = await bot.get_chat_member(order['channel_id'], uid)
        if member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            
            # 1. Update User Credits & Joined List
            await users.update_one({"user_id": uid}, {
                "$inc": {"credits": JOIN_REWARD},
                "$push": {"joined_orders": order['channel_id']}
            })
            
            # 2. Update Order Progress
            new_done = order['completed'] + 1
            if new_done >= order['subscribers']:
                await orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": "completed", "completed": new_done}})
            else:
                await orders.update_one({"_id": ObjectId(order_id)}, {"$inc": {"completed": 1}})
            
            await cb.message.edit_text(f"✅ Verified! +{JOIN_REWARD} Credits mil gaye.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Next Channel ➡️", callback_data="earn")]]))
        else:
            await cb.answer(NOT_JOINED_MSG, show_alert=True)
    except UserNotParticipant:
        await cb.answer(NOT_JOINED_MSG, show_alert=True)
    except Exception:
        await cb.answer("Error: Bot channel me admin nahi hai!", show_alert=True)
