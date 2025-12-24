from pyrogram import Client
from db import orders, users
from config import PENALTY_MSG, PENALTY_CREDITS

@Client.on_chat_member_updated()
async def on_leave(bot, update):
    # Agar user leave kare
    if update.old_chat_member and not update.new_chat_member:
        uid = update.from_user.id
        cid = update.chat.id
        
        # Check active order
        order = await orders.find_one({"channel_id": cid, "status": "active"})
        if order:
            user = await users.find_one({"user_id": uid})
            if cid in user.get("joined_orders", []):
                await users.update_one({"user_id": uid}, {
                    "$inc": {"credits": -PENALTY_CREDITS},
                    "$pull": {"joined_orders": cid}
                })
                try: 
                    await bot.send_message(uid, PENALTY_MSG.format(title=update.chat.title, penalty=PENALTY_CREDITS))
                except: pass
