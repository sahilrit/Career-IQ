"""Generic, zero-dependency document storage backed by SQLite.

Every CareerOS package that needs persistence stores its domain objects
here as JSON documents keyed by ``(entity_type, id)``, rather than each
package inventing its own schema/migration story this early. Typed
repositories (e.g. ``careeros_career_brain``'s ``CareerBrainRepository``)
sit on top of this and own (de)serializing their own pydantic models.

SQLite is part of the Python standard library, so this works with zero
external services and zero paid dependencies — a real, durable local
store out of the box. A future phase can add a Postgres-backed
implementation of the same interface for multi-node deployments without
domain code changing.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from careeros_common.exceptions import CareerOSError


class DocumentNotFoundError(CareerOSError):
    """Raised when a document lookup by (entity_type, id) fails."""


class DocumentStore:
    """A minimal document store: ``(entity_type, id) -> JSON blob``, on SQLite.

    Pass ``":memory:"`` (the default) for an ephemeral store, e.g. in tests.
    """

    def __init__(self, path: str | Path = ":memory:") -> None:
        self._path = str(path)
        if self._path != ":memory:":
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                entity_type TEXT NOT NULL,
                id TEXT NOT NULL,
                data TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (entity_type, id)
            )
            """
        )
        self._conn.commit()

    def put(self, entity_type: str, entity_id: str, data: dict[str, Any]) -> None:
        self._conn.execute(
            """
            INSERT INTO documents (entity_type, id, data, updated_at)
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(entity_type, id) DO UPDATE SET
                data = excluded.data, updated_at = excluded.updated_at
            """,
            (entity_type, entity_id, json.dumps(data)),
        )
        self._conn.commit()

    def get(self, entity_type: str, entity_id: str) -> dict[str, Any]:
        row = self._conn.execute(
            "SELECT data FROM documents WHERE entity_type = ? AND id = ?",
            (entity_type, entity_id),
        ).fetchone()
        if row is None:
            raise DocumentNotFoundError(f"No {entity_type!r} document with id={entity_id!r}")
        return json.loads(row[0])

    def get_or_none(self, entity_type: str, entity_id: str) -> dict[str, Any] | None:
        try:
            return self.get(entity_type, entity_id)
        except DocumentNotFoundError:
            return None

    def delete(self, entity_type: str, entity_id: str) -> None:
        self._conn.execute(
            "DELETE FROM documents WHERE entity_type = ? AND id = ?",
            (entity_type, entity_id),
        )
        self._conn.commit()

    def list(self, entity_type: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT data FROM documents WHERE entity_type = ? ORDER BY updated_at",
            (entity_type,),
        ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> DocumentStore:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
