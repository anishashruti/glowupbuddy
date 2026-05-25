"""
Telegram Webhook Route

Returns 200 OK immediately (within ~50ms), sends instant ack to user,
then runs the appropriate flow as an asyncio background task.

Voice message flow:
  1. POST /webhook received
  2. Send ack: "🌱 Got it, building your day..."
  3. Return 200 OK  ← Telegram sees this within 1s
  4. Background: run morning_flow → send full plan when done (~10–15s)
"""

import asyncio
from datetime import date

from fastapi import APIRouter, Request

from config.database import get_db
from services.bingo import check_square, get_board, get_square_info, render_grid
from services.intent_router import route
from services.telegram_sender import download_voice, send_message
from services.user_profile import get_preferences, set_active_projects

router = APIRouter(prefix="/telegram", tags=["telegram"])


def _format_plan(plan: dict) -> str:
    parts = [f"🎯 *Goal:* {plan['key_goal']}"]
    if plan.get("todos"):
        lines = "\n".join(f"  • {t}" for t in plan["todos"])
        parts.append(f"✅ *Today's todos*\n{lines}")
    if plan.get("bingo_pick"):
        parts.append(f"🎲 *Bingo pick:* {plan['bingo_pick']}")
    if plan.get("experimental_nudge"):
        parts.append(f"✨ *Try this:* {plan['experimental_nudge']}")
    tone_map = {
        "energized": "⚡ Energized",
        "focused": "🔍 Focused",
        "gentle": "🌿 Gentle",
        "rest": "😴 Rest day",
    }
    tone = tone_map.get(plan.get("tone", ""), "")
    if tone:
        parts.append(f"🌡 *Vibe:* {tone}")
    return "\n\n".join(parts)


def _format_extraction(extraction: dict) -> str:
    parts = []
    if extraction.get("transcript"):
        parts.append(f"📝 *Heard:* {extraction['transcript']}")
    mood = extraction.get("mood", "neutral")
    if mood and mood != "neutral":
        parts.append(f"🌡 *Mood:* {mood}")
    if extraction.get("new_tasks"):
        lines = "\n".join(f"  • {t}" for t in extraction["new_tasks"])
        parts.append(f"✅ *Tasks noted:*\n{lines}")
    if extraction.get("ideas"):
        lines = "\n".join(f"  • {i}" for i in extraction["ideas"])
        parts.append(f"💡 *Ideas captured:*\n{lines}")
    return "\n\n".join(parts) if parts else "Got it! I've saved your note."


async def _run_morning_flow(chat_id: str, text: str, audio_bytes: bytes | None) -> None:
    """Background task: run morning_flow via ADK runner, send result."""
    from flows.morning_flow import morning_flow
    from main import get_runner

    runner = get_runner()
    session_id = f"{chat_id}_{date.today().isoformat()}"

    try:
        # Ensure session exists with user_id in initial state
        try:
            session = await runner.session_service.get_session(
                app_name="glowupbuddy", user_id=chat_id, session_id=session_id
            )
        except Exception:
            session = None

        if not session:
            await runner.session_service.create_session(
                app_name="glowupbuddy",
                user_id=chat_id,
                session_id=session_id,
                state={"user_id": chat_id},
            )
        else:
            # Refresh user_id in state for this run
            session.state["user_id"] = chat_id

        # Store input in state before running
        # (audio_bytes passed via state for BaseAgent access)
        if audio_bytes:
            session = await runner.session_service.get_session(
                app_name="glowupbuddy", user_id=chat_id, session_id=session_id
            )
            session.state["audio_bytes"] = audio_bytes
            session.state["input_text"] = ""
        else:
            session = await runner.session_service.get_session(
                app_name="glowupbuddy", user_id=chat_id, session_id=session_id
            )
            session.state["audio_bytes"] = None
            session.state["input_text"] = text

        from google.genai.types import Content, Part

        message = Content(parts=[Part(text=text or "(voice message)")])

        final_state = {}
        async for event in runner.run_async(
            user_id=chat_id,
            session_id=session_id,
            new_message=message,
        ):
            if event.is_final_response() and event.content:
                # Collect final state after all agents have run
                pass

        # Read results from session state
        session = await runner.session_service.get_session(
            app_name="glowupbuddy", user_id=chat_id, session_id=session_id
        )
        extraction = session.state.get("extraction", {})
        daily_plan = session.state.get("daily_plan")

        intake_text = _format_extraction(extraction)
        if daily_plan:
            reply = f"{intake_text}\n\n---\n\n{_format_plan(daily_plan)}"
        else:
            reply = intake_text

        await send_message(chat_id, reply)

    except Exception as e:
        print(f"[morning_flow_bg] error for {chat_id}: {e}")
        await send_message(chat_id, "⚠️ Something went wrong building your plan. Try again?")


async def _run_plan_only(chat_id: str) -> None:
    """Background task: run data_fetcher + plan_composer only (no voice intake)."""
    from agents.data_fetcher_agents import data_fetcher
    from agents.plan_composer_agent import PlanComposerAgent
    from google.adk.agents import SequentialAgent
    from main import get_runner

    # Build a mini plan-only flow
    plan_flow = SequentialAgent(
        name="plan_only_flow",
        sub_agents=[data_fetcher, PlanComposerAgent()],
    )

    from google.adk.runners import InMemoryRunner
    from google.genai.types import Content, Part

    runner = InMemoryRunner(agent=plan_flow, app_name="glowupbuddy_plan")
    session_id = f"{chat_id}_plan_{date.today().isoformat()}"
    await runner.session_service.create_session(
        app_name="glowupbuddy_plan",
        user_id=chat_id,
        session_id=session_id,
        state={
            "user_id": chat_id,
            "extraction": {"mood": "neutral", "new_tasks": []},
        },
    )

    async for event in runner.run_async(
        user_id=chat_id,
        session_id=session_id,
        new_message=Content(parts=[Part(text="/plan")]),
    ):
        pass

    session = await runner.session_service.get_session(
        app_name="glowupbuddy_plan", user_id=chat_id, session_id=session_id
    )
    daily_plan = session.state.get("daily_plan")
    if daily_plan:
        await send_message(chat_id, _format_plan(daily_plan))
    else:
        await send_message(chat_id, "⚠️ Could not generate a plan right now. Try again?")


@router.post("/webhook")
async def webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return {"status": "ignored"}

    message = payload.get("message", {})
    chat_id = str(message.get("chat", {}).get("id", ""))
    if not chat_id:
        return {"status": "ignored"}

    # Gate on registered users
    db = get_db()
    user = db["users"].find_one({"telegram_id": chat_id})
    if not user:
        await send_message(chat_id, "👋 Welcome to GlowUpBuddy! Let's get you set up.")
        return {"status": "ok"}

    voice = message.get("voice")
    text = message.get("text", "")

    intent_result = route(text=text, has_voice=bool(voice))

    # --- Direct (synchronous) intents — fast, no LLM needed ---

    if intent_result.intent == "check_square":
        _, msg = check_square(chat_id, intent_result.params["square_id"])
        await send_message(chat_id, msg)
        return {"status": "ok"}

    if intent_result.intent == "bingo_square":
        board = get_board(chat_id)
        msg = get_square_info(board, intent_result.params["square_id"]) if board else "No bingo board found."
        await send_message(chat_id, msg)
        return {"status": "ok"}

    if intent_result.intent == "bingo_grid":
        board = get_board(chat_id)
        msg = render_grid(board) if board else "No bingo board found. Ask your admin to seed it! 🎯"
        await send_message(chat_id, msg)
        return {"status": "ok"}

    if intent_result.intent == "set_focus":
        projects = intent_result.params.get("projects", [])
        set_active_projects(chat_id, projects)
        await send_message(
            chat_id,
            f"✅ Focus set to: *{', '.join(projects)}*\n\nSend /plan to see your updated schedule.",
        )
        return {"status": "ok"}

    if intent_result.intent == "profile":
        prefs = get_preferences(chat_id)
        if not prefs:
            await send_message(chat_id, "No preferences set yet.\n\nTry `/focus ProjectName` to set your focus.")
        else:
            lines = ["⚙️ *Your Profile*\n"]
            if prefs.get("active_projects"):
                lines.append(f"🎯 Focus: {', '.join(prefs['active_projects'])}")
            if prefs.get("chronotype"):
                lines.append(f"🌅 Chronotype: {prefs['chronotype']}")
            if prefs.get("work_style"):
                lines.append(f"💼 Work style: {prefs['work_style']}")
            await send_message(chat_id, "\n".join(lines))
        return {"status": "ok"}

    # --- Async intents — send ack immediately, process in background ---

    if intent_result.intent == "morning_flow":
        # Send instant ack before doing any work
        await send_message(chat_id, "🌱 Got it, building your day...")

        # Download voice asynchronously if needed, then fire background task
        audio_bytes = None
        if voice:
            audio_bytes = await download_voice(voice["file_id"])

        asyncio.create_task(_run_morning_flow(chat_id, text, audio_bytes))
        return {"status": "ok"}  # ← returned within ~1s

    if intent_result.intent == "plan":
        await send_message(chat_id, "📋 Pulling your plan together...")
        asyncio.create_task(_run_plan_only(chat_id))
        return {"status": "ok"}

    return {"status": "ignored"}
