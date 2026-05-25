from pydantic import BaseModel


class TimeBlock(BaseModel):
    time: str
    task: str
    category: str  # "calendar" | "project" | "personal"


class PlanResult(BaseModel):
    greeting: str
    priorities: list[str]
    blocks: list[TimeBlock]
    notes: str = ""


class DailyPlan(BaseModel):
    key_goal: str
    todos: list[str]          # max 6 (busy), max 4 (tired)
    bingo_pick: str           # label of one unchecked bingo square
    experimental_nudge: str   # one small, novel thing to try
    tone: str                 # "energized" | "focused" | "gentle" | "rest"
