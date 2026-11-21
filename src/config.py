import os
import sys
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
ALLOWED_USER_IDS_RAW = os.getenv("ALLOWED_USER_IDS", "")

if not BOT_TOKEN:
    sys.exit("Error: Missing TELEGRAM_BOT_TOKEN in .env")

if not LINEAR_API_KEY:
    sys.exit("Error: Missing LINEAR_API_KEY in .env")

ALLOWED_USER_IDS = [
    int(uid.strip()) for uid in ALLOWED_USER_IDS_RAW.split(",") if uid.strip().isdigit()
]

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)


def is_authorized(user_id: int) -> bool:
    if not ALLOWED_USER_IDS:
        return True
    return user_id in ALLOWED_USER_IDS
