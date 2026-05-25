"""
Tests for agents/plan_composer.py — User Story 11.

All external calls (Gemini, MongoDB, Calendar, Obsidian) are mocked so
tests run with zero network/DB access.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.plan_composer import TIRED_MOODS, run

# ---------------------------------------------------------------------------
# Shared mock data
# ---------------------------------------------------------------------------

MOCK_BINGO = {
    "squares": [
        {"id": 1, "label": "Paint something outside"},
        {"id": 3, "label": "Crochet for 30 minutes"},
        {"id": 5, "label": "Water your plants"},
        {"id": 7, "label": "Cook a new recipe"},
    ],
    "checked": [13],  # only FREE pre-checked
}

MOCK_PREFS = {
    "chronotype": "morning",
    "active_projects": ["GlowUpBuddy"],
    "work_style": "deep work",
}

MOCK_OBSIDIAN = [
    {"title": "Build plan composer", "column": "In Progress", "board_name": "GlowUpBuddy"},
    {"title": "Write tests", "column": "Testing", "board_name": "GlowUpBuddy"},
    {"title": "Deploy to Cloud Run", "column": "In Progress", "board_name": "OtherProject"},
]

LIGHT_CALENDAR = [
    {"title": "Team call", "start": "14:00", "end": "14:30"},
]

BUSY_CALENDAR = [
    {"title": "Standup", "start": "09:00", "end": "09:30"},
    {"title": "Design review", "start": "11:00", "end": "12:00"},
    {"title": "1:1 with manager", "start": "14:00", "end": "15:00"},
    {"title": "Sprint planning", "start": "15:30", "end": "17:00"},
]


def _gemini_mock(plan: dict) -> MagicMock:
    resp = MagicMock()
    resp.text = json.dumps(plan)
    client = MagicMock()
    client.aio.models.generate_content = AsyncMock(return_value=resp)
    return client


def _patch_all(calendar=None, obsidian=None, bingo=MOCK_BINGO, prefs=MOCK_PREFS, gemini_plan=None):
    """Return a list of context managers that mock all external dependencies."""
    if calendar is None:
        calendar = LIGHT_CALENDAR
    if obsidian is None:
        obsidian = MOCK_OBSIDIAN
    if gemini_plan is None:
        gemini_plan = {
            "key_goal": "Make progress on GlowUpBuddy",
            "todos": ["Write tests", "Fix double fetch"],
            "bingo_pick": "Paint something outside",
            "experimental_nudge": "Take a walk between tasks",
            "tone": "focused",
        }
    return [
        patch("agents.plan_composer._get_client", return_value=_gemini_mock(gemini_plan)),
        patch("agents.plan_composer.get_calendar_events", return_value=calendar),
        patch("agents.plan_composer.get_obsidian_tasks", return_value=obsidian),
        patch("agents.plan_composer.get_bingo_board", return_value=bingo),
        patch("agents.plan_composer.get_user_profile", return_value=prefs),
        patch("agents.plan_composer.save_daily_plan"),
    ]


# ---------------------------------------------------------------------------
# Scenario 1 — Tired mood → max 4 tasks, gentle/rest tone
# ---------------------------------------------------------------------------

async def test_tired_mood_caps_todos_at_4():
    gemini_plan = {
        "key_goal": "Rest and do what you can today",
        "todos": ["Reply to emails", "Short meeting prep", "One quick review", "Drink water"],
        "bingo_pick": "Water your plants",
        "experimental_nudge": "Take a 10-min nap if you need it",
        "tone": "gentle",
    }
    patches = _patch_all(calendar=LIGHT_CALENDAR, gemini_plan=gemini_plan)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        state = await run({
            "user_id": "user_tired",
            "extraction": {"mood": "tired", "new_tasks": ["reply to emails", "short meeting prep"]},
        })

    plan = state["daily_plan"]
    assert len(plan["todos"]) <= 4
    assert plan["tone"] in ("gentle", "rest")
    assert plan["key_goal"]
    assert plan["bingo_pick"]


async def test_tired_mood_enforces_cap_even_if_gemini_returns_more():
    """Code must truncate to max_tasks=4 even when Gemini ignores the instruction."""
    gemini_plan = {
        "key_goal": "Do your best",
        "todos": ["task1", "task2", "task3", "task4", "task5", "task6"],
        "bingo_pick": "Paint something outside",
        "experimental_nudge": "Stretch",
        "tone": "gentle",
    }
    patches = _patch_all(gemini_plan=gemini_plan)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        state = await run({
            "user_id": "user_tired2",
            "extraction": {"mood": "exhausted", "new_tasks": []},
        })

    assert len(state["daily_plan"]["todos"]) == 4  # max_tasks for TIRED_MOODS


async def test_all_tired_mood_values_trigger_cap():
    """Every word in TIRED_MOODS should produce max_tasks=4."""
    for mood in TIRED_MOODS:
        gemini_plan = {
            "key_goal": "Rest",
            "todos": ["t1", "t2", "t3", "t4", "t5"],
            "bingo_pick": "Paint something outside",
            "experimental_nudge": "Rest",
            "tone": "rest",
        }
        patches = _patch_all(gemini_plan=gemini_plan)
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
            state = await run({"user_id": "u", "extraction": {"mood": mood, "new_tasks": []}})
        assert len(state["daily_plan"]["todos"]) <= 4, f"Failed for mood='{mood}'"


# ---------------------------------------------------------------------------
# Scenario 2 — Energized mood, clear calendar → up to 6 tasks
# ---------------------------------------------------------------------------

async def test_energized_mood_allows_6_tasks():
    gemini_plan = {
        "key_goal": "Finish the GlowUpBuddy plan composer end-to-end",
        "todos": ["Write tests", "Fix double fetch", "Deploy backend", "Update README",
                  "Seed bingo board", "Send demo to team"],
        "bingo_pick": "Cook a new recipe",
        "experimental_nudge": "Stand up and work from a different spot today",
        "tone": "energized",
    }
    patches = _patch_all(calendar=[], gemini_plan=gemini_plan)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        state = await run({
            "user_id": "user_energized",
            "extraction": {
                "mood": "excited",
                "new_tasks": ["finish presentation", "send proposal", "update website"],
            },
        })

    plan = state["daily_plan"]
    assert len(plan["todos"]) <= 6
    assert plan["tone"] in ("energized", "focused")


# ---------------------------------------------------------------------------
# Scenario 3 — Busy calendar (3+ events) → task cap reduced by 1
# ---------------------------------------------------------------------------

async def test_busy_calendar_reduces_task_cap():
    gemini_plan = {
        "key_goal": "Survive the meeting marathon",
        "todos": ["Prep for design review", "Send notes after standup", "Quick inbox triage"],
        "bingo_pick": "Crochet for 30 minutes",
        "experimental_nudge": "Block 15 min after last meeting to decompress",
        "tone": "focused",
    }
    patches = _patch_all(calendar=BUSY_CALENDAR, gemini_plan=gemini_plan)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        state = await run({
            "user_id": "user_busy",
            "extraction": {"mood": "neutral", "new_tasks": ["prep for meeting", "send notes"]},
        })

    plan = state["daily_plan"]
    # neutral mood = 6, busy calendar (4 events ≥ 3) = 6 - 1 = 5
    assert len(plan["todos"]) <= 5
    assert plan["key_goal"]


async def test_tired_and_busy_calendar_combines_caps():
    """Tired (cap=4) + busy calendar (−1) → cap=3."""
    gemini_plan = {
        "key_goal": "Get through the day",
        "todos": ["t1", "t2", "t3", "t4", "t5"],
        "bingo_pick": "Paint something outside",
        "experimental_nudge": "Rest between meetings",
        "tone": "gentle",
    }
    patches = _patch_all(calendar=BUSY_CALENDAR, gemini_plan=gemini_plan)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        state = await run({
            "user_id": "user_tired_busy",
            "extraction": {"mood": "tired", "new_tasks": []},
        })

    assert len(state["daily_plan"]["todos"]) <= 3  # max(1, 4 - 1)


# ---------------------------------------------------------------------------
# Scenario 4 — No context (new user, nothing configured)
# ---------------------------------------------------------------------------

async def test_no_context_produces_fallback_plan():
    """Empty calendar, no obsidian tasks, no bingo, no prefs → still returns a valid plan."""
    gemini_plan = {
        "key_goal": "Pick one thing and make it count",
        "todos": ["Check your priorities", "Block one hour of focused work"],
        "bingo_pick": "",
        "experimental_nudge": "Write down three things you want to accomplish this week",
        "tone": "focused",
    }
    patches = _patch_all(calendar=[], obsidian=[], bingo=None, prefs={}, gemini_plan=gemini_plan)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        state = await run({"user_id": "new_user", "extraction": {}})

    plan = state["daily_plan"]
    assert plan["key_goal"]
    assert isinstance(plan["todos"], list)
    assert plan["tone"]


async def test_gemini_failure_returns_fallback_plan():
    """When Gemini throws, run() should not raise — return hardcoded fallback instead."""
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(side_effect=Exception("API down"))

    with patch("agents.plan_composer._get_client", return_value=mock_client), \
         patch("agents.plan_composer.get_calendar_events", return_value=[]), \
         patch("agents.plan_composer.get_obsidian_tasks", return_value=[]), \
         patch("agents.plan_composer.get_bingo_board", return_value=None), \
         patch("agents.plan_composer.get_user_profile", return_value={}), \
         patch("agents.plan_composer.save_daily_plan"):
        state = await run({"user_id": "user_apifail", "extraction": {"mood": "neutral"}})

    plan = state["daily_plan"]
    assert plan["key_goal"]
    assert len(plan["todos"]) >= 1
    assert plan["tone"] == "focused"


# ---------------------------------------------------------------------------
# Scenario 5 — Anxious mood with heavy project load → gentle tone
# ---------------------------------------------------------------------------

async def test_anxious_mood_with_heavy_projects_uses_gentle_tone():
    heavy_obsidian = [
        {"title": "Rewrite entire auth system", "column": "In Progress", "board_name": "GlowUpBuddy"},
        {"title": "Migrate database schema", "column": "In Progress", "board_name": "GlowUpBuddy"},
        {"title": "Refactor all routes", "column": "Testing", "board_name": "GlowUpBuddy"},
    ]
    gemini_plan = {
        "key_goal": "Take it one step at a time",
        "todos": ["Pick just one task and start small", "Take breaks between focus blocks"],
        "bingo_pick": "Water your plants",
        "experimental_nudge": "Write how you are feeling before opening your laptop",
        "tone": "gentle",
    }
    patches = _patch_all(obsidian=heavy_obsidian, gemini_plan=gemini_plan)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        state = await run({
            "user_id": "user_anxious",
            "extraction": {
                "mood": "anxious",
                "new_tasks": ["take a break", "just rest today"],
            },
        })

    plan = state["daily_plan"]
    assert plan["tone"] in ("gentle", "rest")
    assert len(plan["todos"]) <= 4


# ---------------------------------------------------------------------------
# Plan structure & persistence
# ---------------------------------------------------------------------------

async def test_plan_always_has_required_fields():
    gemini_plan = {
        "key_goal": "Ship it",
        "todos": ["Deploy", "Test"],
        "bingo_pick": "Cook a new recipe",
        "experimental_nudge": "Try writing left-handed",
        "tone": "focused",
    }
    patches = _patch_all(gemini_plan=gemini_plan)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5]:
        state = await run({"user_id": "u", "extraction": {"mood": "neutral", "new_tasks": []}})

    plan = state["daily_plan"]
    assert "key_goal" in plan
    assert "todos" in plan
    assert "bingo_pick" in plan
    assert "experimental_nudge" in plan
    assert "tone" in plan


async def test_plan_saved_to_mongodb_and_state():
    gemini_plan = {
        "key_goal": "Ship it",
        "todos": ["Deploy"],
        "bingo_pick": "Paint something outside",
        "experimental_nudge": "Walk",
        "tone": "focused",
    }
    with patch("agents.plan_composer._get_client", return_value=_gemini_mock(gemini_plan)), \
         patch("agents.plan_composer.get_calendar_events", return_value=[]), \
         patch("agents.plan_composer.get_obsidian_tasks", return_value=[]), \
         patch("agents.plan_composer.get_bingo_board", return_value=MOCK_BINGO), \
         patch("agents.plan_composer.get_user_profile", return_value={}), \
         patch("agents.plan_composer.save_daily_plan") as mock_save:
        state = await run({"user_id": "user_save", "extraction": {"mood": "neutral"}})

    # saved to MongoDB
    mock_save.assert_called_once()
    call_user_id, call_plan = mock_save.call_args[0]
    assert call_user_id == "user_save"
    assert call_plan["key_goal"] == "Ship it"

    # also in state
    assert state["daily_plan"]["key_goal"] == "Ship it"


# ---------------------------------------------------------------------------
# Active project filtering (in-memory, no second DB call)
# ---------------------------------------------------------------------------

async def test_active_projects_filter_applied_in_memory():
    """Obsidian tasks from boards not in active_projects should be excluded."""
    prefs_with_filter = {"active_projects": ["GlowUpBuddy"]}
    gemini_plan = {
        "key_goal": "Focus on GlowUpBuddy",
        "todos": ["Build plan composer"],
        "bingo_pick": "Paint something outside",
        "experimental_nudge": "Stand",
        "tone": "focused",
    }
    with patch("agents.plan_composer._get_client", return_value=_gemini_mock(gemini_plan)), \
         patch("agents.plan_composer.get_calendar_events", return_value=[]), \
         patch("agents.plan_composer.get_obsidian_tasks", return_value=MOCK_OBSIDIAN) as mock_obs, \
         patch("agents.plan_composer.get_bingo_board", return_value=MOCK_BINGO), \
         patch("agents.plan_composer.get_user_profile", return_value=prefs_with_filter), \
         patch("agents.plan_composer.save_daily_plan"):
        await run({"user_id": "u", "extraction": {"mood": "neutral"}})

    # get_obsidian_tasks called exactly ONCE (no second fetch)
    assert mock_obs.call_count == 1


async def test_voice_tasks_appear_in_extraction_passed_to_prompt():
    """new_tasks from voice intake must be present in state["extraction"] consumed by run()."""
    captured_prompt = {}

    async def fake_generate(model, contents, config):
        captured_prompt["text"] = contents
        resp = MagicMock()
        resp.text = json.dumps({
            "key_goal": "Done",
            "todos": ["task"],
            "bingo_pick": "Paint something outside",
            "experimental_nudge": "Walk",
            "tone": "focused",
        })
        return resp

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = fake_generate

    with patch("agents.plan_composer._get_client", return_value=mock_client), \
         patch("agents.plan_composer.get_calendar_events", return_value=[]), \
         patch("agents.plan_composer.get_obsidian_tasks", return_value=[]), \
         patch("agents.plan_composer.get_bingo_board", return_value=MOCK_BINGO), \
         patch("agents.plan_composer.get_user_profile", return_value={}), \
         patch("agents.plan_composer.save_daily_plan"):
        await run({
            "user_id": "u",
            "extraction": {"mood": "neutral", "new_tasks": ["finish the slide deck", "send email"]},
        })

    assert "finish the slide deck" in captured_prompt["text"]
    assert "send email" in captured_prompt["text"]
