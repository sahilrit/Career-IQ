"""Postgres-backed document store — the same ``(entity_type, id) -> JSON``
interface as the SQLite ``DocumentStore``, for multi-node deployments.

psycopg is imported lazily so ``careeros_common`` keeps zero mandatory
third-party dependencies (the zero-cost constraint): only installs that
actually point at Postgres pull it in. A connection pool makes this safe
under the concurrent requests a web server produces — unlike a single
shared SQLite connection.
"""

from __future__ import annotations

from typing import Any

from careeros_common.storage import DocumentNotFoundError

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS documents (
    entity_type TEXT NOT NULL,
    id TEXT NOT NULL,
    data JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (entity_type, id)
)
"""


class PostgresDocumentStore:
    """Drop-in replacement for ``DocumentStore`` backed by Postgres."""

    def __init__(self, dsn: str, *, min_size: int = 1, max_size: int = 10) -> None:
        try:
            from psycopg_pool import ConnectionPool
        except ImportError as error:  # pragma: no cover - only hit without the extra
            raise RuntimeError(
                "Postgres support needs psycopg — install careeros-api/dashboard "
                "with their Postgres dependencies (psycopg[binary], psycopg-pool)."
            ) from error
        self._pool = ConnectionPool(dsn, min_size=min_size, max_size=max_size, open=True)
        with self._pool.connection() as conn:
            conn.execute(_CREATE_TABLE)

    def put(self, entity_type: str, entity_id: str, data: dict[str, Any]) -> None:
        from psycopg.types.json import Jsonb

        with self._pool.connection() as conn:
            conn.execute(
                """
                INSERT INTO documents (entity_type, id, data, updated_at)
                VALUES (%s, %s, %s, now())
                ON CONFLICT (entity_type, id)
                DO UPDATE SET data = EXCLUDED.data, updated_at = EXCLUDED.updated_at
                """,
                (entity_type, entity_id, Jsonb(data)),
            )

    def get(self, entity_type: str, entity_id: str) -> dict[str, Any]:
        with self._pool.connection() as conn:
            row = conn.execute(
                "SELECT data FROM documents WHERE entity_type = %s AND id = %s",
                (entity_type, entity_id),
            ).fetchone()
        if row is None:
            raise DocumentNotFoundError(f"No {entity_type!r} document with id={entity_id!r}")
        return row[0]  # psycopg parses JSONB into a Python dict

    def get_or_none(self, entity_type: str, entity_id: str) -> dict[str, Any] | None:
        try:
            return self.get(entity_type, entity_id)
        except DocumentNotFoundError:
            return None

    def delete(self, entity_type: str, entity_id: str) -> None:
        with self._pool.connection() as conn:
            conn.execute(
                "DELETE FROM documents WHERE entity_type = %s AND id = %s",
                (entity_type, entity_id),
            )

    def list(self, entity_type: str) -> list[dict[str, Any]]:
        with self._pool.connection() as conn:
            rows = conn.execute(
                "SELECT data FROM documents WHERE entity_type = %s ORDER BY updated_at",
                (entity_type,),
            ).fetchall()
        return [row[0] for row in rows]

    def close(self) -> None:
        self._pool.close()

    def __enter__(self) -> PostgresDocumentStore:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
