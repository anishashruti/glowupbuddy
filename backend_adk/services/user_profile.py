from config.database import get_db


def get_preferences(user_id: str) -> dict:
    db = get_db()
    user = db["users"].find_one({"telegram_id": user_id}, {"preferences": 1, "_id": 0})
    return (user or {}).get("preferences", {})


def update_preferences(user_id: str, updates: dict) -> None:
    db = get_db()
    db["users"].update_one(
        {"telegram_id": user_id},
        {"$set": {f"preferences.{k}": v for k, v in updates.items()}},
    )


def set_active_projects(user_id: str, projects: list[str]) -> None:
    update_preferences(user_id, {"active_projects": projects})
