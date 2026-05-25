from datetime import date, datetime, timezone

from config.database import get_db
from services.bingo import get_board
from services.user_profile import get_preferences


def get_bingo_board(user_id: str) -> dict | None:
    """Returns current month's bingo board for user."""
    return get_board(user_id)


def get_user_profile(user_id: str) -> dict:
    """Returns user preferences dict."""
    return get_preferences(user_id)


def save_daily_plan(user_id: str, plan: dict) -> None:
    """Upserts daily plan into MongoDB daily_plans collection."""
    db = get_db()
    db["daily_plans"].update_one(
        {"user_id": user_id, "date": date.today().isoformat()},
        {"$set": {
            "user_id": user_id,
            "date": date.today().isoformat(),
            "plan": plan,
            "updated_at": datetime.now(timezone.utc),
        }},
        upsert=True,
    )
