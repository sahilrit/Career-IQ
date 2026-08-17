"""One place that decides which document store backs the app.

- ``CAREEROS_DATABASE_URL`` set (``postgres://…``) -> PostgresDocumentStore
  (multi-node production).
- otherwise -> SQLite ``DocumentStore`` at ``CAREEROS_DATA_DIR`` (local /
  single-node self-hosted).

Both expose the identical ``put/get/get_or_none/delete/list`` interface,
so every repository and the tenant-scoping wrapper work unchanged either
way.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from careeros_common.storage import DocumentStore

DEFAULT_DATA_DIR = Path(".careeros/data")


def database_url() -> str | None:
    url = os.environ.get("CAREEROS_DATABASE_URL", "").strip()
    return url or None


def open_store() -> Any:
    """Open the configured document store (Postgres if a DATABASE_URL is
    set, else SQLite). Returns something with the DocumentStore interface."""
    url = database_url()
    if url:
        from careeros_common.postgres_storage import PostgresDocumentStore

        return PostgresDocumentStore(url)
    data_dir = Path(os.environ.get("CAREEROS_DATA_DIR", str(DEFAULT_DATA_DIR)))
    return DocumentStore(data_dir / "careeros.db")
