import asyncio
import json

from google import genai
from google.genai import types

from config.settings import GEMINI_API_KEY, GCP_PROJECT
from models.plan import DailyPlan
from tools.calendar_tools import get_calendar_events
from tools.mongo_tools import get_bingo_board, get_user_profile, save_daily_plan
from tools.obsidian_tools import get_obsidian_tasks

_client: genai.Client | None = None

TIRED_MOODS = {"tired", "exhausted", "drained", "anxious", "sad", "low"}

_PROMPT = """You are a kind personal growth assistant. Generate a mood-aware daily plan.

MOOD: {mood}
MAX TODOS: {max_tasks} (enforce this limit strictly — do not exceed it)

TASKS FROM TODAY'S MESSAGE:
{new_tasks}

CALENDAR EVENTS TODAY:
{calendar}

ACTIVE PROJECT TASKS (from Obsidian):
{obsidian}

BINGO BOARD — pick ONE unchecked square label:
{bingo}

USER PREFERENCES:
{preferences}

Rules:
- key_goal: the single most important thing to accomplish today
- todos: max {max_tasks} items — prioritise ruthlessly
- bingo_pick: pick exactly one unchecked square label from the bingo board above
- experimental_nudge: one small, novel, unexpected thing (e.g. "take your next call standing outside")
- tone: one of "energized" | "focused" | "gentle" | "rest"
  • tired/exhausted/anxious mood → tone="gentle" or "rest", light tasks only
  • energized/happy mood → tone="energized", up to {max_tasks} todos
  • busy calendar (3+ events) → reduce todos by 1
- Return ONLY valid JSON, no markdown:
{{
  "key_goal": "...",
  "todos": ["...", "..."],
  "bingo_pick": "...",
  "experimental_nudge": "...",
  "tone": "..."
}}"""


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if GEMINI_API_KEY:
            _client = genai.Client(api_key=GEMINI_API_KEY)
        else:
            _client = genai.Client(vertexai=True, project=GCP_PROJECT, location="us-central1")
    return _client


def _fmt_calendar(events: list[dict]) -> str:
    if not events:
        return "No calendar events today."
    return "\n".join(f"- {e['start']} → {e['end']}: {e['title']}" for e in events)


def _fmt_obsidian(tasks: list[dict]) -> str:
    if not tasks:
        return "No active project tasks."
    return "\n".join(f"- [{t['column']}] {t['title']} ({t['board_name']})" for t in tasks)


def _fmt_bingo(board: dict | None) -> str:
    if not board:
        return "No bingo board found."
    squares = board.get("squares", [])
    checked = set(board.get("checked", []))
    lines = [
        f"- {s['label']} (id={s['id']})"
        for s in squares
        if s["id"] not in checked
    ]
    return "\n".join(lines) if lines else "All squares checked!"


def _fmt_new_tasks(tasks: list[str]) -> str:
    if not tasks:
        return "None."
    return "\n".join(f"- {t}" for t in tasks)


def _fmt_preferences(prefs: dict) -> str:
    if not prefs:
        return "No preferences set yet."
    lines = []
    if prefs.get("chronotype"):
        lines.append(f"Chronotype: {prefs['chronotype']}")
    if prefs.get("active_projects"):
        lines.append(f"Focus projects: {', '.join(prefs['active_projects'])}")
    if prefs.get("work_style"):
        lines.append(f"Work style: {prefs['work_style']}")
    if prefs.get("avoid"):
        avoid = prefs["avoid"] if isinstance(prefs["avoid"], list) else [prefs["avoid"]]
        lines.append(f"Avoid: {'; '.join(avoid)}")
    if prefs.get("notes"):
        lines.append(f"Notes: {prefs['notes']}")
    return "\n".join(lines) if lines else "No preferences set yet."


async def run(state: dict) -> dict:
    """
    Accepts state dict with at least {"user_id": str}.
    Reads state["extraction"] for mood if present.
    Returns state with state["daily_plan"] added.
    """
    user_id = state["user_id"]
    extraction = state.get("extraction", {})
    mood = extraction.get("mood", "neutral") or "neutral"
    new_tasks = extraction.get("new_tasks", [])

    # All 4 reads in parallel
    calendar, obsidian, bingo, prefs = await asyncio.gather(
        asyncio.to_thread(get_calendar_events),
        asyncio.to_thread(get_obsidian_tasks, user_id),
        asyncio.to_thread(get_bingo_board, user_id),
        asyncio.to_thread(get_user_profile, user_id),
    )

    # Filter obsidian in-memory by active_projects (avoids a second DB round-trip)
    active_projects = prefs.get("active_projects") or None
    if active_projects:
        obsidian = [
            t for t in obsidian
            if any(p.lower() in t["board_name"].lower() for p in active_projects)
        ]

    # Mood-aware task cap
    max_tasks = 4 if mood.lower() in TIRED_MOODS else 6
    if len(calendar) >= 3:
        max_tasks = max(1, max_tasks - 1)

    prompt = _PROMPT.format(
        mood=mood,
        max_tasks=max_tasks,
        new_tasks=_fmt_new_tasks(new_tasks),
        calendar=_fmt_calendar(calendar),
        obsidian=_fmt_obsidian(obsidian),
        bingo=_fmt_bingo(bingo),
        preferences=_fmt_preferences(prefs),
    )

    try:
        response = await _get_client().aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        data = json.loads(response.text)
        plan = DailyPlan(
            key_goal=data.get("key_goal", "Make progress on your top priority"),
            todos=data.get("todos", [])[:max_tasks],
            bingo_pick=data.get("bingo_pick", ""),
            experimental_nudge=data.get("experimental_nudge", ""),
            tone=data.get("tone", "focused"),
        )
    except Exception as e:
        print(f"[plan_composer] Gemini error: {e}")
        plan = DailyPlan(
            key_goal="Focus on your most important task",
            todos=["Check your calendar", "Pick one project task to complete"],
            bingo_pick="",
            experimental_nudge="Step outside for 5 minutes before starting work.",
            tone="focused",
        )

    save_daily_plan(user_id, plan.model_dump())
    state["daily_plan"] = plan.model_dump()
    return state
