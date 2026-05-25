from datetime import date

from services.calendar import get_todays_events


def get_calendar_events(target_date: str | None = None) -> list[dict]:
    """Returns calendar events as [{title, start, end}]. Accepts ISO date string or None for today."""
    d = date.fromisoformat(target_date) if target_date else None
    return get_todays_events(target_date=d)
