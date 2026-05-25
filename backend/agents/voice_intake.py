import json
from datetime import datetime, timezone, date as date_type
from pathlib import Path

from google import genai
from google.genai import types

from config.database import get_db
from config.settings import GEMINI_API_KEY, GCP_PROJECT
from models.extraction import ExtractionResult

_client: genai.Client | None = None

EXTRACTIONS_DIR = Path(__file__).parent.parent / "extractions"


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if GEMINI_API_KEY:
            print(f"[voice_intake] Using AI Studio key: {GEMINI_API_KEY[:10]}...")
            _client = genai.Client(api_key=GEMINI_API_KEY)
        else:
            print(f"[voice_intake] Using Vertex AI — project: {GCP_PROJECT}")
            _client = genai.Client(vertexai=True, project=GCP_PROJECT, location="us-central1")
    return _client


_PROMPT = """You are a personal growth assistant. Analyze the input and extract structured information.
Return ONLY valid JSON with this exact schema:
{
  "transcript": "<full transcription if audio input, null if text input>",
  "mood": "<single word: happy/stressed/focused/tired/excited/anxious/motivated/neutral>",
  "new_tasks": ["<task the person wants or needs to do>"],
  "ideas": ["<creative thought, plan, or concept mentioned>"],
  "progress_updates": ["<something already done or currently in progress>"]
}
Return ONLY the JSON object, no markdown, no explanation."""


async def run(chat_id: str, text: str = "", audio_bytes: bytes | None = None) -> ExtractionResult:
    source = "voice" if audio_bytes else "text"
    try:
        if audio_bytes:
            contents = [
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/ogg"),
                _PROMPT,
            ]
        else:
            contents = f"{_PROMPT}\n\nInput:\n{text}"

        response = await _get_client().aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        result = ExtractionResult(**json.loads(response.text))
    except Exception as e:
        print(f"[voice_intake] Gemini error: {e}")
        result = ExtractionResult()

    _save_to_file(chat_id, result, source, raw_input=text, model="gemini-2.5-flash")
    _save_to_db(chat_id, result, source)
    return result


def _save_to_file(chat_id: str, result: ExtractionResult, source: str, raw_input: str = "", model: str = "gemini-2.0-flash") -> None:
    EXTRACTIONS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = EXTRACTIONS_DIR / f"{chat_id}_{timestamp}.txt"
    lines = [
        f"user_id   : {chat_id}",
        f"date      : {date_type.today().isoformat()}",
        f"source    : {source}",
        f"model     : {model}",
        f"timestamp : {datetime.now(timezone.utc).isoformat()}",
        f"raw_input : {raw_input or '(voice note)'}",
        "",
        f"transcript       : {result.transcript or '(voice — see raw_input)'}",
        f"mood             : {result.mood}",
        f"new_tasks        : {result.new_tasks}",
        f"ideas            : {result.ideas}",
        f"progress_updates : {result.progress_updates}",
    ]
    file_path.write_text("\n".join(lines))


def _save_to_db(chat_id: str, result: ExtractionResult, source: str) -> None:
    try:
        db = get_db()
        db["reflections"].insert_one({
            "user_id": chat_id,
            "date": date_type.today().isoformat(),
            "source": source,
            "extraction": result.model_dump(),
            "created_at": datetime.now(timezone.utc),
        })
        if result.new_tasks:
            db["tasks"].insert_many([
                {
                    "user_id": chat_id,
                    "title": task,
                    "source": source,
                    "status": "pending",
                    "date": date_type.today().isoformat(),
                    "created_at": datetime.now(timezone.utc),
                }
                for task in result.new_tasks
            ])
    except Exception:
        pass
