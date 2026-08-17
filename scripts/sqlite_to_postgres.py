"""One-time copy of every document from a SQLite CareerOS database into
Postgres. Both stores share the (entity_type, id, data) schema, so this
is a straight row-by-row transfer.

Usage:
    CAREEROS_DATABASE_URL=postgresql://user:pass@host/db \
        uv run python scripts/sqlite_to_postgres.py --sqlite .careeros/data/careeros.db [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sqlite3

from careeros_common import database_url
from careeros_common.postgres_storage import PostgresDocumentStore


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite", default=".careeros/data/careeros.db")
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()

    url = database_url()
    if not url:
        raise SystemExit("Set CAREEROS_DATABASE_URL to the target Postgres database.")

    source = sqlite3.connect(arguments.sqlite)
    rows = source.execute("SELECT entity_type, id, data FROM documents").fetchall()
    source.close()
    print(f"Found {len(rows)} document(s) in {arguments.sqlite}.")

    if arguments.dry_run:
        print("Dry run — nothing written.")
        return

    target = PostgresDocumentStore(url)
    try:
        for entity_type, entity_id, data in rows:
            target.put(entity_type, entity_id, json.loads(data))
    finally:
        target.close()
    print(f"Copied {len(rows)} document(s) into Postgres.")


if __name__ == "__main__":
    main()
