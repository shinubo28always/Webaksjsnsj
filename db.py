import os
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL, ADMIN_IDS

# --- Database Connection Setup ---
client = AsyncIOMotorClient(MONGO_URL)
# Aapka bataya hua database name
database = client["DogeshBhai_S4S_Bot"]

# --- Collections ---
users = database.users
orders = database.orders
admins = database.admins

# ================= USER HELPERS =================

async def get_user(uid: int):
    """User ki details nikalta hai, agar nahi hai toh naya banata hai."""
    user = await users.find_one({"user_id": uid})
    if not user:
        user = {
            "user_id": uid,
            "credits": 10,           # New user joining bonus
            "joined_orders": [],     # Jo channels user ne join kiye hain
            "referred_by": None,     # Kisne refer kiya
            "step": None,            # Bot ke flow ko track karne ke liye
            "temp_data": None        # Temporary storage (like channel link/id)
        }
        await users.insert_one(user)
    return user

async def get_user_data(uid: int):
    """Sirf user ka data return karta hai (get_user ka shortcut)."""
    return await users.find_one({"user_id": uid})

# ================= STEP MANAGEMENT =================

async def set_step(uid: int, step: str, temp=None):
    """
    User ka current step set karta hai.
    Example steps: 'WAIT_CHANNEL', 'WAIT_CREDITS', None
    """
    update_data = {"$set": {"step": step}}
    if temp is not None:
        update_data["$set"]["temp_data"] = temp
    else:
        # Agar temp pass nahi kiya toh purana wala clear kar do (safety ke liye)
        update_data["$set"]["temp_data"] = None
        
    await users.update_one({"user_id": uid}, update_data)

# ================= ADMIN HELPERS =================

async def is_admin(uid: int):
    """Check karta hai ki user admin hai ya nahi (Config + DB)."""
    # 1. Config wale Super Admins check karo
    if uid in ADMIN_IDS:
        return True
    
    # 2. Database wale Admins check karo
    admin = await admins.find_one({"user_id": uid})
    if admin:
        return True
        
    return False

# ================= CREDIT HELPERS =================

async def add_credits(uid: int, amount: int):
    """User ke balance mein credits add karta hai."""
    await users.update_one({"user_id": uid}, {"$inc": {"credits": amount}})

async def use_credits(uid: int, amount: int):
    """User ke balance se credits minus karta hai."""
    await users.update_one({"user_id": uid}, {"$inc": {"credits": -amount}})
