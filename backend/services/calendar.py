from datetime import date, datetime, timezone
from pathlib import Path

from config.settings import CALENDAR_TOKEN_PATH

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def get_todays_events(target_date: date | None = None) -> list[dict]:
    token_path = Path(CALENDAR_TOKEN_PATH)
    if not token_path.exists():
        print(f"[calendar] token.json not found at {token_path} — skipping")
        return []

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.write_text(creds.to_json())

        service = build("calendar", "v3", credentials=creds)

        today = target_date or date.today()
        time_min = datetime(today.year, today.month, today.day, 0, 0, 0, tzinfo=timezone.utc).isoformat()
        time_max = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=timezone.utc).isoformat()

        result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = []
        for e in result.get("items", []):
            start = e.get("start", {})
            end = e.get("end", {})
            events.append({
                "title": e.get("summary", "Untitled"),
                "start": start.get("dateTime", start.get("date", "")),
                "end": end.get("dateTime", end.get("date", "")),
            })
        return events

    except Exception as e:
        print(f"[calendar] Error fetching events: {e}")
        return []
