import re
from datetime import datetime, timezone
from calendar import month_name

from config.database import get_db

GRID_SIZE = 5
FREE_ID = 13


def get_board(user_id: str) -> dict | None:
    db = get_db()
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    return db["bingo_boards"].find_one({"user_id": user_id, "month": month}, {"_id": 0})


def check_square(user_id: str, square_id: int) -> tuple[bool, str]:
    """Mark a square as checked. Returns (success, message)."""
    board = get_board(user_id)
    if not board:
        return False, "No bingo board found for this month."

    if square_id == FREE_ID:
        return False, "That's the FREE square — it's already yours! ⭐"

    squares = {s["id"]: s for s in board["squares"]}
    if square_id not in squares:
        return False, f"Square {square_id} doesn't exist. Pick a number between 1–25."

    if square_id in board["checked"]:
        label = squares[square_id]["label"]
        return False, f"You already checked off *{label}* ✅"

    db = get_db()
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    db["bingo_boards"].update_one(
        {"user_id": user_id, "month": month},
        {"$addToSet": {"checked": square_id}}
    )

    label = squares[square_id]["label"]
    done = len(board["checked"]) + 1 - 1  # subtract FREE
    return True, f"✅ Checked off *{label}*!\n{done}/24 done this month 🎉"


def get_square_info(board: dict, square_id: int) -> str:
    squares = {s["id"]: s for s in board["squares"]}
    if square_id not in squares:
        return f"Square {square_id} doesn't exist. Pick 1–25."
    if square_id == FREE_ID:
        return "⭐ Square 13 is your FREE space!"
    sq = squares[square_id]
    checked = "✅" if square_id in board["checked"] else "⬜"
    return f"{checked} *{square_id}.* {sq['label']}"


def render_grid(board: dict) -> str:
    checked = set(board["checked"])
    month_str = month_name[int(board["month"].split("-")[1])]

    rows = []
    for row in range(GRID_SIZE):
        cells = []
        for col in range(GRID_SIZE):
            sq_id = row * GRID_SIZE + col + 1
            if sq_id == FREE_ID:
                cells.append("⭐")
            elif sq_id in checked:
                cells.append("✅")
            else:
                cells.append("⬜")
        rows.append(" ".join(cells))

    done = len(checked) - 1  # subtract FREE
    grid = "\n".join(rows)

    return (
        f"🎯 *{month_str} Bingo Board*\n\n"
        f"{grid}\n\n"
        f"*{done}/24 done*\n\n"
        f'Type `bingo 5` to see what square 5 is\n'
        f'Type `check 5` to mark it done'
    )
