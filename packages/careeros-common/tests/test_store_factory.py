"""Tests for the store factory and the Postgres store.

The SQLite path runs everywhere. The Postgres path runs only when
CAREEROS_TEST_DATABASE_URL points at a real database (e.g. in CI with a
Postgres service) — otherwise it's skipped, not failed.
"""

from __future__ import annotations

import os

import pytest

from careeros_common import DocumentStore, database_url, open_store


def test_factory_returns_sqlite_without_a_database_url(monkeypatch, tmp_path):
    monkeypatch.delenv("CAREEROS_DATABASE_URL", raising=False)
    monkeypatch.setenv("CAREEROS_DATA_DIR", str(tmp_path))
    store = open_store()
    assert isinstance(store, DocumentStore)
    store.put("widget", "1", {"name": "gadget"})
    assert store.get("widget", "1") == {"name": "gadget"}
    store.close()


def test_database_url_reads_env(monkeypatch):
    monkeypatch.setenv("CAREEROS_DATABASE_URL", "postgres://x")
    assert database_url() == "postgres://x"
    monkeypatch.setenv("CAREEROS_DATABASE_URL", "  ")
    assert database_url() is None


_PG_URL = os.environ.get("CAREEROS_TEST_DATABASE_URL")


@pytest.mark.skipif(not _PG_URL, reason="no CAREEROS_TEST_DATABASE_URL for a live Postgres")
def test_postgres_store_roundtrips_and_lists():
    from careeros_common.postgres_storage import PostgresDocumentStore

    store = PostgresDocumentStore(_PG_URL)
    try:
        store.put("widget", "a", {"n": 1})
        store.put("widget", "b", {"n": 2})
        assert store.get("widget", "a") == {"n": 1}
        assert store.get_or_none("widget", "missing") is None
        listed = store.list("widget")
        assert {"n": 1} in listed and {"n": 2} in listed
        store.delete("widget", "a")
        assert store.get_or_none("widget", "a") is None
    finally:
        store.close()
