"""
Seed the monthly bingo board for a user.

Usage:
    uv run python scripts/seed_bingo.py --user-id <telegram_id>

Run this once at the start of each month (or automate via cron).
"""

import argparse
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

SQUARES = [
    {"id": 1,  "label": "Paint something you see outside your window 🎨", "category": "painting"},
    {"id": 2,  "label": "Try a new watercolor technique",                  "category": "painting"},
    {"id": 3,  "label": "Crochet for 30 minutes while listening to music 🧶", "category": "crochet"},
    {"id": 4,  "label": "Start a tiny new crochet project",                "category": "crochet"},
    {"id": 5,  "label": "Water all your plants and talk to them 🌱",       "category": "gardening"},
    {"id": 6,  "label": "Repot or propagate something",                    "category": "gardening"},
    {"id": 7,  "label": "Cook a recipe you have never tried before 🍳",    "category": "cooking"},
    {"id": 8,  "label": "Make something from scratch — no shortcuts",      "category": "cooking"},
    {"id": 9,  "label": "Sketch something from your daily life ✏️",        "category": "sketching"},
    {"id": 10, "label": "Fill a full page in your sketchbook",             "category": "sketching"},
    {"id": 11, "label": "Update your portfolio with one new piece 💼",     "category": "portfolio"},
    {"id": 12, "label": "Write 3 things you are proud of about your work", "category": "portfolio"},
    {"id": 13, "label": "FREE ⭐",                                          "category": "free"},
    {"id": 14, "label": "Film a 60-second vlog of your day 🎬",            "category": "vlogging"},
    {"id": 15, "label": "Post one piece of content you have been putting off", "category": "vlogging"},
    {"id": 16, "label": "Go to a local market or community event 🛍️",     "category": "social"},
    {"id": 17, "label": "Do something spontaneous with a friend",          "category": "social"},
    {"id": 18, "label": "Watch a film in a language you do not speak 🎥",  "category": "movies"},
    {"id": 19, "label": "Watch a TV episode in a new language with subtitles", "category": "movies"},
    {"id": 20, "label": "Spend a full hour on a creative hobby — no phone","category": "wildcard"},
    {"id": 21, "label": "Try something creative you have never done before","category": "wildcard"},
    {"id": 22, "label": "Visit a park or garden for inspiration 🌸",       "category": "outdoors"},
    {"id": 23, "label": "Sit outside and just observe for 10 minutes",     "category": "outdoors"},
    {"id": 24, "label": "Write about something that made you smile this month", "category": "reflection"},
    {"id": 25, "label": "Take a photo of something beautiful you noticed today 📸", "category": "reflection"},
]


def seed(user_id: str) -> None:
    mongo_uri = os.environ.get("MONGO_URI")
    mongo_db = os.getenv("MONGO_DB_NAME", "glowupbuddy")
    if not mongo_uri:
        print("[error] MONGO_URI not set")
        sys.exit(1)

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=15000)
    client.admin.command("ping")
    db = client[mongo_db]

    month = datetime.now(timezone.utc).strftime("%Y-%m")
    doc = {
        "user_id": user_id,
        "month": month,
        "squares": SQUARES,
        "checked": [13],    # FREE is pre-checked
        "created_at": datetime.now(timezone.utc),
    }

    db["bingo_boards"].update_one(
        {"user_id": user_id, "month": month},
        {"$setOnInsert": doc},
        upsert=True,
    )
    print(f"✅ Bingo board seeded for user '{user_id}' — {month}")
    client.close()


def main():
    parser = argparse.ArgumentParser(description="Seed monthly bingo board")
    parser.add_argument("--user-id", default=os.getenv("GLOWUP_USER_ID"))
    args = parser.parse_args()

    if not args.user_id:
        print("[error] --user-id or GLOWUP_USER_ID required")
        sys.exit(1)

    seed(args.user_id)


if __name__ == "__main__":
    main()
