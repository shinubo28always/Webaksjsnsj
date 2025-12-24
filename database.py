from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL

mongo = AsyncIOMotorClient(MONGO_URL)
db = mongo["DogeshBhai_S4S_Bot"]
users = db.users
orders = db.orders

async def get_user(uid: int):
    user = await users.find_one({"user_id": uid})
    if not user:
        user = {
            "user_id": uid, 
            "credits": 10, 
            "joined_orders": [], 
            "referred_by": None
        }
        await users.insert_one(user)
    return user
