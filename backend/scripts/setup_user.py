import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database import get_db

db = get_db()
db["users"].update_one(
    {"telegram_id": "8798045167"},
    {"$setOnInsert": {"telegram_id": "8798045167", "name": "Anisha", "onboarding_complete": True}},
    upsert=True,
)
print("User created")

print("Users:", db["users"].count_documents({}))
print("Reflections:", db["reflections"].count_documents({}))
print("Projects:", db["projects"].count_documents({}))
print("Bingo boards:", db["bingo_boards"].count_documents({}))

r = db["reflections"].find_one(sort=[("created_at", -1)])
if r:
    print("\nLatest reflection:")
    print("  source:", r.get("source"))
    print("  mood:", r.get("extraction", {}).get("mood"))
    print("  tasks:", r.get("extraction", {}).get("new_tasks"))
