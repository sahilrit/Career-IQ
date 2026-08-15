"""One-time migration: move pre-SaaS single-tenant data into a workspace.

Before auth, the dashboard and CLI wrote documents with bare entity
types ("career_brain", "calendar_event", ...). Under SaaS mode every
page reads through a TenantScopedDocumentStore, which only sees
"tenant:<workspace_id>:<entity_type>" — so existing data becomes
invisible until it's rescoped.

Usage:
    1. Sign up in the dashboard, then find your workspace id on the
       Admin page (or in the tenancy_workspace table).
    2. uv run python scripts/migrate_to_workspace.py --workspace-id <ID>
       [--data-dir .careeros/data] [--dry-run]

Global entity types (tenancy, auth, subscriptions) are never touched.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

# Platform-level records that must stay unscoped.
GLOBAL_PREFIXES = ("tenancy_", "auth_", "tenant:")
GLOBAL_TYPES = {"subscription"}


def migrate(db_path: Path, workspace_id: str, *, dry_run: bool) -> list[tuple[str, int]]:
    connection = sqlite3.connect(db_path)
    try:
        rows = connection.execute("SELECT DISTINCT entity_type FROM documents").fetchall()
        moved: list[tuple[str, int]] = []
        for (entity_type,) in rows:
            if entity_type in GLOBAL_TYPES or entity_type.startswith(GLOBAL_PREFIXES):
                continue
            scoped = f"tenant:{workspace_id}:{entity_type}"
            count = connection.execute(
                "SELECT COUNT(*) FROM documents WHERE entity_type = ?", (entity_type,)
            ).fetchone()[0]
            if not dry_run:
                connection.execute(
                    "UPDATE documents SET entity_type = ? WHERE entity_type = ?",
                    (scoped, entity_type),
                )
            moved.append((entity_type, count))
        if not dry_run:
            connection.commit()
        return moved
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--data-dir", default=".careeros/data")
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()

    db_path = Path(arguments.data_dir) / "careeros.db"
    if not db_path.exists():
        raise SystemExit(f"No database at {db_path}")

    moved = migrate(db_path, arguments.workspace_id, dry_run=arguments.dry_run)
    verb = "Would move" if arguments.dry_run else "Moved"
    if not moved:
        print("Nothing to migrate — all data is already scoped or global.")
    for entity_type, count in moved:
        print(f"{verb} {count:4d} document(s): {entity_type}")


if __name__ == "__main__":
    main()
