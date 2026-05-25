"""
Intent Router — classifies incoming Telegram messages and routes them.

Returns an IntentResult that tells the webhook handler what to do:
  - "morning_flow"  → run morning_flow pipeline (voice or text with tasks)
  - "plan"          → run data_fetcher + plan_composer only (no voice intake)
  - "bingo_grid"    → show full bingo grid
  - "bingo_square"  → show info for a specific square
  - "check_square"  → mark a bingo square done
  - "set_focus"     → update active_projects preference
  - "profile"       → show user profile/preferences
  - "unknown"       → no-op / ignore
"""

import re
from dataclasses import dataclass, field


@dataclass
class IntentResult:
    intent: str
    params: dict = field(default_factory=dict)


def route(text: str, has_voice: bool) -> IntentResult:
    """Classify a Telegram message into an intent."""

    if has_voice:
        return IntentResult(intent="morning_flow")

    cmd = text.strip().lower()

    # Explicit plan command
    if cmd in ("/plan", "plan"):
        return IntentResult(intent="plan")

    # Check a bingo square: "check 5"
    if m := re.fullmatch(r"check\s+(\d+)", cmd):
        return IntentResult(intent="check_square", params={"square_id": int(m.group(1))})

    # Info on a bingo square: "bingo 5"
    if m := re.fullmatch(r"bingo\s+(\d+)", cmd):
        return IntentResult(intent="bingo_square", params={"square_id": int(m.group(1))})

    # Full bingo grid: "bingo" or "/bingo"
    if cmd in ("bingo", "/bingo"):
        return IntentResult(intent="bingo_grid")

    # Set focus projects: "/focus ProjectA, ProjectB"
    if cmd.startswith("/focus ") or cmd.startswith("focus on "):
        raw = cmd.replace("/focus ", "").replace("focus on ", "")
        projects = [p.strip() for p in re.split(r"[,&]|\band\b", raw) if p.strip()]
        return IntentResult(intent="set_focus", params={"projects": projects})

    # Show profile
    if cmd in ("/profile", "profile"):
        return IntentResult(intent="profile")

    # Anything else with meaningful text → treat as morning intake
    if text.strip():
        return IntentResult(intent="morning_flow")

    return IntentResult(intent="unknown")
