"""Shared Telegram messaging utility used by routes and background tasks."""

import httpx

from config.settings import TELEGRAM_BOT_TOKEN

_TG_API = "https://api.telegram.org"


async def send_message(chat_id: str | int, text: str) -> None:
    """Send a Telegram message. Silently ignores failures."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"{_TG_API}/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            )
    except Exception as e:
        print(f"[telegram_sender] Failed to send to {chat_id}: {e}")


async def download_voice(file_id: str) -> bytes | None:
    """Download a Telegram voice file by file_id. Returns bytes or None on failure."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{_TG_API}/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
            )
            file_path = r.json()["result"]["file_path"]
            audio = await client.get(
                f"{_TG_API}/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
            )
            return audio.content
    except Exception as e:
        print(f"[telegram_sender] Voice download failed: {e}")
        return None
