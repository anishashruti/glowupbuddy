"""
One-time Google Calendar OAuth2 authorization.
Run once: uv run python scripts/setup_calendar_auth.py
Saves token.json to the backend/ directory.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
BACKEND_DIR = Path(__file__).parent.parent


def main():
    secrets = list(BACKEND_DIR.glob("client_secret_*.json"))
    if not secrets:
        print("[error] No client_secret_*.json found in backend/")
        sys.exit(1)

    creds_file = secrets[0]
    print(f"Using credentials: {creds_file.name}")

    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
    creds = flow.run_local_server(port=0)

    token_path = BACKEND_DIR / "token.json"
    token_path.write_text(creds.to_json())
    print(f"✅ Token saved to {token_path}")
    print("Add to .env: CALENDAR_TOKEN_PATH=token.json")


if __name__ == "__main__":
    main()
