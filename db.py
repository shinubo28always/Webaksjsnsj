import os
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL, ADMIN_IDS

# --- Database Connection ---
client = AsyncIOMotorClient(MONGO_URL)
# Aapka bataya hua database name
database = client["DogeshBhai_S4S_Bot"]

# --- Collections ---
users = database.users
orders = database.orders
admins = database.admins

# ================= USER DATA HELPERS =================

async def get_user(uid: int):
    """User ki details nikalta hai, agar nahi hai toh naya banata hai."""
    user = await users.find_one({"user_id": uid})
    if not user:
        user = {
            "user_id": uid,
            "credits": 10,           # New user joining bonus
            "joined_orders": [],     # Jo channels user ne join kiye hain
            "referred_by": None,     # Referral tracking
            "step": None,            # Current state (e.g., WAIT_CH, WAIT_CR)
            "temp_data": None        # Channel info temporary store karne ke liye
        }
        await users.insert_one(user)
    return user

async def get_user_data(uid: int):
    """Sirf user ka data return karta hai (Searching ke liye)."""
    return await users.find_one({"user_id": uid})

# ================= STATE/STEP MANAGEMENT =================

async def set_step(uid: int, step: str, temp=None):
    """
    User ka 'step' update karta hai taki bot ko context pata ho.
    temp: Channel title, ID, aur link save karne ke liye.
    """
    await users.update_one(
        {"user_id": uid},
        {"$set": {"step": step, "temp_data": temp}},
        upsert=True
    )

async def get_step(uid: int):
    """User ka current step check karne ke liye."""
    user = await users.find_one({"user_id": uid})
    return user.get("step") if user else None

# ================= ADMIN LOGIC =================

async def is_admin(uid: int):
    """Check karta hai ki user admin hai ya nahi (Super Admin + DB Admin)."""
    # 1. Check from Config.py (Super Admins)
    if uid in ADMIN_IDS:
        return True
    
    # 2. Check from MongoDB (Added Admins)
    admin = await admins.find_one({"user_id": uid})
    return True if admin else False

# ================= CREDIT HELPERS =================

async def add_credits(uid: int, amount: int):
    """Credits badhane ke liye."""
    await users.update_one({"user_id": uid}, {"$inc": {"credits": amount}})

async def use_credits(uid: int, amount: int):
    """Credits ghatane ke liye."""
    await users.update_one({"user_id": uid}, {"$inc": {"credits": -amount}})
