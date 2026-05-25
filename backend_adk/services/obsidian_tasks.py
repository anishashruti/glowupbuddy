from config.database import get_db

_COLUMN_PRIORITY = {"In Progress": 0, "Testing": 1}


def get_obsidian_tasks(
    user_id: str,
    active_projects: list[str] | None = None,
    limit_per_project: int = 2,
) -> list[dict]:
    """
    Return prioritised active tasks from Obsidian boards.
    Filters to active_projects if set, caps at limit_per_project per board,
    and sorts In Progress before Testing before other columns.
    """
    db = get_db()
    boards = list(db["projects"].find({"user_id": user_id, "source": "obsidian"}))

    tasks = []
    for board in boards:
        board_name = board.get("board_name", "")

        if active_projects:
            if not any(p.lower() in board_name.lower() for p in active_projects):
                continue

        active = [t for t in board.get("tasks", []) if not t.get("done")]
        active.sort(key=lambda t: _COLUMN_PRIORITY.get(t.get("column", ""), 2))

        for task in active[:limit_per_project]:
            tasks.append({
                "title": task["title"],
                "column": task["column"],
                "board_name": board_name,
            })
    return tasks
