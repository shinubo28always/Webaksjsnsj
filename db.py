from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL, ADMIN_IDS

# Connection
client = AsyncIOMotorClient(MONGO_URL)
database = client["DogeshBhai_S4S_Bot"]

# Collections
users = database.users
orders = database.orders
admins = database.admins

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

async def is_admin(uid):
    # Pehle check karo Super Admin (Config se)
    if uid in ADMIN_IDS:
        return True
    # Phir check karo Database wale Admins
    admin = await admins.find_one({"user_id": uid})
    return True if admin else False
