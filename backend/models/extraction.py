from pydantic import BaseModel
from typing import Optional


class ExtractionResult(BaseModel):
    transcript: Optional[str] = None
    mood: str = "neutral"
    new_tasks: list[str] = []
    ideas: list[str] = []
    progress_updates: list[str] = []
