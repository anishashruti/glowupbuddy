"""
Plan Composer Agent — ADK BaseAgent

Reads all data from session state (extraction, calendar, obsidian, bingo, prefs),
calls Gemini to generate a mood-aware DailyPlan, saves to MongoDB,
writes to state["daily_plan"].
"""

import json

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.genai import Client
from google.genai import types

from config.settings import GEMINI_API_KEY, GCP_PROJECT
from models.plan import DailyPlan
from tools.mongo_tools import save_daily_plan

TIRED_MOODS = {"tired", "exhausted", "drained", "anxious", "sad", "low"}

_PROMPT = """You are a kind personal growth assistant. Generate a mood-aware daily plan.

MOOD: {mood}
MAX TODOS: {max_tasks} (enforce this strictly — do not exceed it)

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
- key_goal: the single most important thing today
- todos: max {max_tasks} items — prioritise ruthlessly
- bingo_pick: exactly one unchecked label from bingo board above
- experimental_nudge: one small, novel, unexpected thing to try
- tone: "energized" | "focused" | "gentle" | "rest"
  • tired/exhausted/anxious/sad/low → "gentle" or "rest"
  • excited/happy/motivated → "energized"
  • busy calendar (3+ events) → reduce todos by 1
Return ONLY valid JSON, no markdown:
{{
  "key_goal": "...",
  "todos": ["..."],
  "bingo_pick": "...",
  "experimental_nudge": "...",
  "tone": "..."
}}"""

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        if GEMINI_API_KEY:
            _client = Client(api_key=GEMINI_API_KEY)
        else:
            _client = Client(vertexai=True, project=GCP_PROJECT, location="us-central1")
    return _client


def _fmt_list(items: list) -> str:
    return "\n".join(f"- {i}" for i in items) if items else "None."


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
    checked = set(board.get("checked", []))
    lines = [
        f"- {s['label']} (id={s['id']})"
        for s in board.get("squares", [])
        if s["id"] not in checked
    ]
    return "\n".join(lines) if lines else "All squares checked!"


def _fmt_prefs(prefs: dict) -> str:
    if not prefs:
        return "No preferences set yet."
    lines = []
    if prefs.get("chronotype"):
        lines.append(f"Chronotype: {prefs['chronotype']}")
    if prefs.get("active_projects"):
        lines.append(f"Focus projects: {', '.join(prefs['active_projects'])}")
    if prefs.get("work_style"):
        lines.append(f"Work style: {prefs['work_style']}")
    return "\n".join(lines) if lines else "No preferences set yet."


class PlanComposerAgent(BaseAgent):
    """
    ADK agent: reads all state, calls Gemini, returns a DailyPlan.

    Reads:  state["extraction"], state["calendar_events"], state["obsidian_tasks"],
            state["bingo_board"], state["user_prefs"], state["user_id"]
    Writes: state["daily_plan"]
    """

    name: str = "plan_composer"
    description: str = "Generates a mood-aware daily plan from all collected context"

    async def _run_async_impl(self, ctx):
        state = ctx.session.state
        user_id = state.get("user_id", "")

        extraction = state.get("extraction", {})
        mood = extraction.get("mood", "neutral") or "neutral"
        new_tasks = extraction.get("new_tasks", [])

        calendar = state.get("calendar_events", [])
        obsidian = state.get("obsidian_tasks", [])
        bingo = state.get("bingo_board")
        prefs = state.get("user_prefs", {})

        # Filter obsidian by active_projects in-memory
        active_projects = prefs.get("active_projects")
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
            new_tasks=_fmt_list(new_tasks),
            calendar=_fmt_calendar(calendar),
            obsidian=_fmt_obsidian(obsidian),
            bingo=_fmt_bingo(bingo),
            preferences=_fmt_prefs(prefs),
        )

        try:
            response = await _get_client().aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            data = json.loads(response.text)
            plan = DailyPlan(
                key_goal=data.get("key_goal", "Focus on your top priority"),
                todos=data.get("todos", [])[:max_tasks],
                bingo_pick=data.get("bingo_pick", ""),
                experimental_nudge=data.get("experimental_nudge", ""),
                tone=data.get("tone", "focused"),
            )
        except Exception as e:
            print(f"[plan_composer_agent] Gemini error: {e}")
            plan = DailyPlan(
                key_goal="Focus on your most important task",
                todos=["Check your calendar", "Pick one project task to complete"],
                bingo_pick="",
                experimental_nudge="Step outside for 5 minutes before starting work.",
                tone="focused",
            )

        if user_id:
            save_daily_plan(user_id, plan.model_dump())

        state["daily_plan"] = plan.model_dump()

        yield Event(
            author=self.name,
            content=types.Content(
                parts=[types.Part(text=f"Plan composed: tone={plan.tone}, tasks={len(plan.todos)}")]
            ),
        )
