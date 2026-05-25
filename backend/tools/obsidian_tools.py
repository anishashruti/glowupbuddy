from services.obsidian_tasks import get_obsidian_tasks as _get


def get_obsidian_tasks(user_id: str, active_projects: list[str] | None = None) -> list[dict]:
    """Returns active Obsidian tasks as [{title, column, board_name}]."""
    return _get(user_id, active_projects=active_projects)
