"""
Voice Intake Agent — ADK BaseAgent

Reads audio bytes or text from session state, calls Gemini for extraction,
writes ExtractionResult to state["extraction"], persists to MongoDB.
"""

import asyncio
import json
from datetime import datetime, timezone, date as date_type

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.genai import Client
from google.genai import types

from config.database import get_db
from config.settings import GEMINI_API_KEY, GCP_PROJECT
from models.extraction import ExtractionResult

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

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        if GEMINI_API_KEY:
            _client = Client(api_key=GEMINI_API_KEY)
        else:
            _client = Client(vertexai=True, project=GCP_PROJECT, location="us-central1")
    return _client


def _persist(user_id: str, extraction: dict) -> None:
    try:
        db = get_db()
        db["reflections"].insert_one({
            "user_id": user_id,
            "date": date_type.today().isoformat(),
            "source": extraction.get("source", "unknown"),
            "extraction": extraction,
            "created_at": datetime.now(timezone.utc),
        })
        if extraction.get("new_tasks"):
            db["tasks"].insert_many([
                {
                    "user_id": user_id,
                    "title": task,
                    "source": extraction.get("source", "unknown"),
                    "status": "pending",
                    "date": date_type.today().isoformat(),
                    "created_at": datetime.now(timezone.utc),
                }
                for task in extraction["new_tasks"]
            ])
    except Exception as e:
        print(f"[voice_intake_agent] DB persist error: {e}")


async def _call_gemini(text: str, audio_bytes: bytes | None) -> ExtractionResult:
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
    return ExtractionResult(**json.loads(response.text))


class VoiceIntakeAgent(BaseAgent):
    """
    ADK agent: transcribes voice or parses text, extracts mood + tasks.

    Reads:  state["input_text"], state["audio_bytes"], state["user_id"]
    Writes: state["extraction"]
    """

    name: str = "voice_intake"
    description: str = "Transcribes voice or parses text and extracts mood, tasks, and ideas"

    async def _run_async_impl(self, ctx):
        state = ctx.session.state
        user_id = state.get("user_id", "")
        text = state.get("input_text", "")
        audio_bytes = state.get("audio_bytes")
        source = "voice" if audio_bytes else "text"

        try:
            result = await _call_gemini(text=text, audio_bytes=audio_bytes)
        except Exception as e:
            print(f"[voice_intake_agent] Gemini error: {e}")
            result = ExtractionResult()

        extraction = {**result.model_dump(), "source": source}
        state["extraction"] = extraction

        if user_id:
            await asyncio.to_thread(_persist, user_id, extraction)

        yield Event(
            author=self.name,
            content=types.Content(
                parts=[types.Part(text=f"Extracted mood={result.mood}, tasks={len(result.new_tasks)}")]
            ),
        )
