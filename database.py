from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL
from datetime import date

cluster = AsyncIOMotorClient(MONGO_URL)
db = cluster["SUB_EXCHANGE"]

users = db.users
orders = db.orders

async def get_user(user_id):
    user = await users.find_one({"user_id": user_id})
    if not user:
        user = {
            "user_id": user_id,
            "credits": 10,
            "referred_by": None,
            "joined_orders": [], # List of channel IDs joined
            "daily_date": str(date.today())
        }
        await users.insert_one(user)
    return user

async def add_credits(user_id, amount):
    await users.update_one({"user_id": user_id}, {"$inc": {"credits": amount}})

async def use_credits(user_id, amount):
    await users.update_one({"user_id": user_id}, {"$inc": {"credits": -amount}})
