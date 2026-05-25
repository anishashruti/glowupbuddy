from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    telegram_id: str
    name: str
    email: Optional[str] = None
    chronotype: Optional[str] = None
    task_style: str = "todo"
    onboarding_complete: bool = False


class UserMessage(BaseModel):
    telegram_id: str
    text: str
