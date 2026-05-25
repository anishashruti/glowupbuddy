"""
Morning Flow — ADK SequentialAgent

Step 1: VoiceIntakeAgent    — transcribe/extract from voice or text
Step 2: data_fetcher        — ParallelAgent fan-out (calendar, obsidian, bingo, profile)
Step 3: PlanComposerAgent   — generate mood-aware daily plan

State flow:
  IN  → state["user_id"], state["input_text" | "audio_bytes"]
  S1  → state["extraction"]
  S2  → state["calendar_events"], state["obsidian_tasks"],
         state["bingo_board"],     state["user_prefs"]
  S3  → state["daily_plan"]
"""

from google.adk.agents import SequentialAgent

from agents.data_fetcher_agents import data_fetcher
from agents.plan_composer_agent import PlanComposerAgent
from agents.voice_intake_agent import VoiceIntakeAgent

morning_flow = SequentialAgent(
    name="morning_flow",
    description=(
        "Full morning pipeline: voice/text intake → parallel data fetch → mood-aware plan"
    ),
    sub_agents=[
        VoiceIntakeAgent(),
        data_fetcher,
        PlanComposerAgent(),
    ],
)
