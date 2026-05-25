"""
Obsidian Kanban → MongoDB sync script.

Scans a configured folder inside your Obsidian vault for kanban boards
(files with `kanban-plugin: board` in frontmatter), extracts tasks from
"In Progress" and "Testing" columns, and upserts them into the MongoDB
`projects` collection.

Usage:
    uv run python scripts/obsidian_sync.py

Required env vars (set in .env or shell):
    MONGO_URI              — MongoDB connection string
    MONGO_DB_NAME          — database name (default: glowupbuddy)
    OBSIDIAN_VAULT_PATH    — absolute path to Obsidian vault root
    OBSIDIAN_KANBAN_FOLDER — subfolder within vault containing kanban boards
    GLOWUP_USER_ID         — your user_id in the users collection

Cron (every 30 min):
    */30 * * * * cd /path/to/glowupbuddy/backend && uv run python scripts/obsidian_sync.py >> /tmp/obsidian_sync.log 2>&1
"""

import argparse
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

ACTIVE_COLUMNS = {"in progress", "testing"}


def _strip_wiki_links(text: str) -> str:
    """[[Some Link]] → Some Link"""
    return re.sub(r"\[\[(.+?)\]\]", r"\1", text)


def _parse_kanban(path: Path) -> list[dict] | None:
    """
    Parse a kanban .md file. Returns a list of task dicts for ACTIVE_COLUMNS,
    or None if the file is not a kanban board.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"  [warn] Cannot read {path.name}: {e}")
        return None

    # Strip settings block at the bottom
    content = re.split(r"%%\s*kanban:settings", content)[0]

    # Must have kanban-plugin frontmatter
    if "kanban-plugin: board" not in content:
        return None

    tasks = []
    current_column = None

    for line in content.splitlines():
        # Detect column headers
        heading_match = re.match(r"^##\s*(.*)", line)
        if heading_match:
            current_column = heading_match.group(1).strip().lower()
            continue

        if current_column not in ACTIVE_COLUMNS:
            continue

        # Match task lines: - [ ] or - [x]
        task_match = re.match(r"^- \[([ xX])\]\s+(.+)", line)
        if task_match:
            done = task_match.group(1).lower() == "x"
            title = _strip_wiki_links(task_match.group(2).strip())
            tasks.append({
                "title": title,
                "column": current_column.title(),  # "In Progress" / "Testing"
                "done": done,
            })

    return tasks


def sync(vault_path: Path, kanban_folder: str, user_id: str, db) -> None:
    scan_dir = vault_path / kanban_folder
    if not scan_dir.exists():
        print(f"[error] Kanban folder not found: {scan_dir}")
        sys.exit(1)

    md_files = list(scan_dir.glob("*.md"))
    if not md_files:
        print(f"[warn] No .md files found in {scan_dir}")
        return

    collection = db["projects"]
    synced = 0
    skipped = 0

    for md_file in sorted(md_files):
        tasks = _parse_kanban(md_file)
        if tasks is None:
            print(f"  [skip] {md_file.name} — not a kanban board or unreadable")
            skipped += 1
            continue

        doc = {
            "user_id": user_id,
            "board_name": md_file.stem,
            "source_path": str(md_file),
            "source": "obsidian",
            "tasks": tasks,
            "last_synced": datetime.now(timezone.utc),
        }

        collection.update_one(
            {"user_id": user_id, "source_path": str(md_file)},
            {"$set": doc},
            upsert=True,
        )

        active_count = len(tasks)
        print(f"  [ok] {md_file.name} — {active_count} active task(s)")
        synced += 1

    print(f"\nDone. Synced {synced} board(s), skipped {skipped}.")


def main():
    parser = argparse.ArgumentParser(description="Sync Obsidian kanban boards to MongoDB")
    parser.add_argument("--vault-path", default=os.getenv("OBSIDIAN_VAULT_PATH"))
    parser.add_argument("--kanban-folder", default=os.getenv("OBSIDIAN_KANBAN_FOLDER"))
    parser.add_argument("--user-id", default=os.getenv("GLOWUP_USER_ID"))
    args = parser.parse_args()

    missing = [k for k, v in {
        "vault-path / OBSIDIAN_VAULT_PATH": args.vault_path,
        "kanban-folder / OBSIDIAN_KANBAN_FOLDER": args.kanban_folder,
        "user-id / GLOWUP_USER_ID": args.user_id,
    }.items() if not v]
    if missing:
        print(f"[error] Missing required config: {', '.join(missing)}")
        sys.exit(1)

    mongo_uri = os.environ.get("MONGO_URI")
    mongo_db = os.getenv("MONGO_DB_NAME", "glowupbuddy")
    if not mongo_uri:
        print("[error] MONGO_URI not set")
        sys.exit(1)

    vault_path = Path(args.vault_path).expanduser()
    if not vault_path.exists():
        print(f"[error] Vault path not found: {vault_path}")
        sys.exit(1)

    print(f"Connecting to MongoDB...")
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=15000)
        client.admin.command("ping")
        db = client[mongo_db]
    except Exception as e:
        print(f"[error] MongoDB connection failed: {e}")
        sys.exit(1)

    print(f"Scanning: {vault_path / args.kanban_folder}\n")
    try:
        sync(vault_path, args.kanban_folder, args.user_id, db)
    finally:
        client.close()


if __name__ == "__main__":
    main()
