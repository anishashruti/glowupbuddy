import re

from agents.voice_intake import run as voice_intake_run
from agents.plan_composer import run as plan_composer_run
from services.bingo import get_board, check_square, get_square_info, render_grid
from services.user_profile import get_preferences, set_active_projects, update_preferences
from config.database import get_db


async def handle_message(chat_id: str, text: str = "", audio_bytes: bytes | None = None) -> str:
    db = get_db()
    user = db["users"].find_one({"telegram_id": chat_id})
    if not user:
        return "👋 Welcome to GlowUpBuddy! Let's get you set up."

    cmd = text.strip().lower()

    # "check 5" — mark a square done
    if m := re.fullmatch(r"check\s+(\d+)", cmd):
        _, msg = check_square(chat_id, int(m.group(1)))
        return msg

    # "bingo 5" — show square details
    if m := re.fullmatch(r"bingo\s+(\d+)", cmd):
        board = get_board(chat_id)
        if not board:
            return "No bingo board found. Ask your admin to run the seed script! 🎯"
        return get_square_info(board, int(m.group(1)))

    # "bingo" or "/bingo" — show full grid
    if cmd in ("bingo", "/bingo"):
        board = get_board(chat_id)
        if not board:
            return "No bingo board found. Ask your admin to run the seed script! 🎯"
        return render_grid(board)

    # "/plan" or "plan" — compose daily plan
    if cmd in ("/plan", "plan"):
        last = db["reflections"].find_one({"user_id": chat_id}, sort=[("created_at", -1)])
        state = {
            "user_id": chat_id,
            "extraction": last.get("extraction", {}) if last else {},
        }
        state = await plan_composer_run(state)
        return _format_plan(state["daily_plan"])

    # "/focus ProjectA, ProjectB" — set weekly focus projects
    if cmd.startswith("/focus ") or cmd.startswith("focus on "):
        raw = cmd.replace("/focus ", "").replace("focus on ", "")
        projects = [p.strip() for p in re.split(r"[,&]|\band\b", raw) if p.strip()]
        set_active_projects(chat_id, projects)
        return f"✅ Focus set to: *{', '.join(projects)}*\n\nSend /plan to see your updated schedule."

    # "/profile" — show current preferences
    if cmd in ("/profile", "profile"):
        prefs = get_preferences(chat_id)
        if not prefs:
            return "No preferences set yet.\n\nTry:\n• `/focus ProjectA, ProjectB` — set focus projects\n• Tell me things like *\"I prefer deep work in the mornings\"*"
        lines = ["⚙️ *Your Profile*\n"]
        if prefs.get("active_projects"):
            lines.append(f"🎯 Focus: {', '.join(prefs['active_projects'])}")
        if prefs.get("chronotype"):
            lines.append(f"🌅 Chronotype: {prefs['chronotype']}")
        if prefs.get("work_style"):
            lines.append(f"💼 Work style: {prefs['work_style']}")
        if prefs.get("weekly_fixed"):
            fixed = prefs["weekly_fixed"] if isinstance(prefs["weekly_fixed"], list) else [prefs["weekly_fixed"]]
            lines.append(f"📅 Fixed: {'; '.join(fixed)}")
        if prefs.get("avoid"):
            avoid = prefs["avoid"] if isinstance(prefs["avoid"], list) else [prefs["avoid"]]
            lines.append(f"🚫 Avoid: {'; '.join(avoid)}")
        return "\n".join(lines)

    # everything else — voice/text intake
    result = await voice_intake_run(chat_id=chat_id, text=text, audio_bytes=audio_bytes)

    parts = []
    if result.transcript:
        parts.append(f"📝 *Heard:* {result.transcript}")
    if result.mood and result.mood != "neutral":
        parts.append(f"🌡 *Mood:* {result.mood}")
    if result.new_tasks:
        tasks = "\n".join(f"  • {t}" for t in result.new_tasks)
        parts.append(f"✅ *Tasks noted:*\n{tasks}")
    if result.ideas:
        ideas = "\n".join(f"  • {i}" for i in result.ideas)
        parts.append(f"💡 *Ideas captured:*\n{ideas}")
    if result.progress_updates:
        progress = "\n".join(f"  • {p}" for p in result.progress_updates)
        parts.append(f"🚀 *Progress:*\n{progress}")

    intake_reply = "\n\n".join(parts) if parts else "Got it! I've saved your note."

    # Auto-compose plan after every voice message
    if audio_bytes:
        state = {"user_id": chat_id, "extraction": result.model_dump()}
        state = await plan_composer_run(state)
        return f"{intake_reply}\n\n---\n\n{_format_plan(state['daily_plan'])}"

    return intake_reply


def _format_plan(plan: dict) -> str:
    parts = [f"🎯 *Goal:* {plan['key_goal']}"]

    if plan.get("todos"):
        lines = "\n".join(f"  • {t}" for t in plan["todos"])
        parts.append(f"✅ *Todos*\n{lines}")

    if plan.get("bingo_pick"):
        parts.append(f"🎲 *Bingo pick:* {plan['bingo_pick']}")

    if plan.get("experimental_nudge"):
        parts.append(f"✨ *Try this:* {plan['experimental_nudge']}")

    tone_label = {"energized": "⚡ Energized", "focused": "🔍 Focused",
                  "gentle": "🌿 Gentle", "rest": "😴 Rest day"}.get(plan.get("tone", ""), "")
    if tone_label:
        parts.append(f"🌡 *Tone:* {tone_label}")

    return "\n\n".join(parts)
