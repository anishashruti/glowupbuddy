import httpx
from fastapi import APIRouter, Request

from config.settings import TELEGRAM_BOT_TOKEN
from services.agent import handle_message

router = APIRouter(prefix="/telegram", tags=["telegram"])

_TG_API = "https://api.telegram.org"


async def _download_voice(file_id: str) -> bytes | None:
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{_TG_API}/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}")
            file_path = r.json()["result"]["file_path"]
            audio = await client.get(f"{_TG_API}/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}")
            return audio.content
    except Exception:
        return None


async def _send_reply(chat_id: int, text: str) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{_TG_API}/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        )


@router.post("/webhook")
async def webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return {"status": "ignored"}
    message = payload.get("message", {})
    chat_id = message.get("chat", {}).get("id")

    if not chat_id:
        return {"status": "ignored"}

    voice = message.get("voice")
    text = message.get("text", "")

    if voice:
        audio_bytes = await _download_voice(voice["file_id"])
        reply = await handle_message(chat_id=str(chat_id), text="", audio_bytes=audio_bytes)
    elif text:
        reply = await handle_message(chat_id=str(chat_id), text=text)
    else:
        return {"status": "ignored"}

    await _send_reply(chat_id, reply)
    return {"status": "ok"}
