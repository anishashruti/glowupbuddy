import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.environ["MONGO_URI"]
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "glowupbuddy")
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GCP_PROJECT = os.getenv("GCP_PROJECT", "glowupbuddy")
CALENDAR_TOKEN_PATH = os.getenv("CALENDAR_TOKEN_PATH", "token.json")
