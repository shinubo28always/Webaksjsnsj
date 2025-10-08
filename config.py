import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    OWNER_ID = int(os.getenv("OWNER_ID", 0))
    TARGET_CHAT_ID =  # 👈 ekhane tumi group/channel ID boshabe (e.g. -1001234567890)
