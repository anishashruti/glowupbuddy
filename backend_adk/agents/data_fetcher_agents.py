"""
Data Fetcher Agents — ADK fan-out with ParallelAgent

4 lightweight BaseAgent subclasses, each fetching one data source.
Assembled into a ParallelAgent so all 4 run concurrently.

Fan-out writes:
  state["calendar_events"]  ← CalendarFetchAgent
  state["obsidian_tasks"]   ← ObsidianFetchAgent
  state["bingo_board"]      ← BingoFetchAgent
  state["user_prefs"]       ← ProfileFetchAgent
"""

import asyncio

from google.adk.agents import BaseAgent, ParallelAgent
from google.adk.events import Event
from google.genai import types

from tools.calendar_tools import get_calendar_events
from tools.mongo_tools import get_bingo_board, get_user_profile
from tools.obsidian_tools import get_obsidian_tasks


class CalendarFetchAgent(BaseAgent):
    """Fetches today's Google Calendar events."""

    name: str = "calendar_fetch"
    description: str = "Fetches today's calendar events"

    async def _run_async_impl(self, ctx):
        try:
            events = await asyncio.to_thread(get_calendar_events)
        except Exception as e:
            print(f"[calendar_fetch] error: {e}")
            events = []

        ctx.session.state["calendar_events"] = events
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=f"Fetched {len(events)} calendar events")]),
        )


class ObsidianFetchAgent(BaseAgent):
    """Fetches active tasks from Obsidian boards in MongoDB."""

    name: str = "obsidian_fetch"
    description: str = "Fetches active Obsidian project tasks"

    async def _run_async_impl(self, ctx):
        user_id = ctx.session.state.get("user_id", "")
        try:
            tasks = await asyncio.to_thread(get_obsidian_tasks, user_id)
        except Exception as e:
            print(f"[obsidian_fetch] error: {e}")
            tasks = []

        ctx.session.state["obsidian_tasks"] = tasks
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=f"Fetched {len(tasks)} Obsidian tasks")]),
        )


class BingoFetchAgent(BaseAgent):
    """Fetches the current month's bingo board."""

    name: str = "bingo_fetch"
    description: str = "Fetches current month's bingo board"

    async def _run_async_impl(self, ctx):
        user_id = ctx.session.state.get("user_id", "")
        try:
            board = await asyncio.to_thread(get_bingo_board, user_id)
        except Exception as e:
            print(f"[bingo_fetch] error: {e}")
            board = None

        ctx.session.state["bingo_board"] = board
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text="Fetched bingo board")]),
        )


class ProfileFetchAgent(BaseAgent):
    """Fetches user preferences from MongoDB."""

    name: str = "profile_fetch"
    description: str = "Fetches user preferences and profile"

    async def _run_async_impl(self, ctx):
        user_id = ctx.session.state.get("user_id", "")
        try:
            prefs = await asyncio.to_thread(get_user_profile, user_id)
        except Exception as e:
            print(f"[profile_fetch] error: {e}")
            prefs = {}

        ctx.session.state["user_prefs"] = prefs
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text="Fetched user profile")]),
        )


# Fan-out: all 4 fetch agents run concurrently
data_fetcher = ParallelAgent(
    name="data_fetcher",
    description="Fan-out: fetches calendar, Obsidian tasks, bingo board, and user prefs in parallel",
    sub_agents=[
        CalendarFetchAgent(),
        ObsidianFetchAgent(),
        BingoFetchAgent(),
        ProfileFetchAgent(),
    ],
)
