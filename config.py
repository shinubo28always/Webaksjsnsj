import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS").split(",")]
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL"))

JOIN_REWARD = 2
REF_REWARD = 5
PENALTY_CREDITS = 10  # Leave karne par kitne katenge
MIN_ORDER_CREDITS = 50
