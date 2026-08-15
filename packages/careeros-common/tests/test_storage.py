"""Tests for the SQLite-backed generic document store."""

from __future__ import annotations

import pytest

from careeros_common.storage import DocumentNotFoundError, DocumentStore


@pytest.fixture
def store():
    with DocumentStore() as s:
        yield s


def test_put_then_get_roundtrips(store):
    store.put("widget", "1", {"name": "gadget"})
    assert store.get("widget", "1") == {"name": "gadget"}


def test_get_missing_raises(store):
    with pytest.raises(DocumentNotFoundError):
        store.get("widget", "does-not-exist")


def test_get_or_none_returns_none_for_missing(store):
    assert store.get_or_none("widget", "does-not-exist") is None


def test_put_overwrites_existing_document(store):
    store.put("widget", "1", {"name": "gadget"})
    store.put("widget", "1", {"name": "gizmo"})
    assert store.get("widget", "1") == {"name": "gizmo"}


def test_delete_removes_document(store):
    store.put("widget", "1", {"name": "gadget"})
    store.delete("widget", "1")
    assert store.get_or_none("widget", "1") is None


def test_list_returns_only_matching_entity_type(store):
    store.put("widget", "1", {"name": "gadget"})
    store.put("gizmo", "1", {"name": "thing"})
    assert store.list("widget") == [{"name": "gadget"}]


def test_entity_types_are_isolated_by_id(store):
    store.put("widget", "shared-id", {"kind": "widget"})
    store.put("gizmo", "shared-id", {"kind": "gizmo"})
    assert store.get("widget", "shared-id") == {"kind": "widget"}
    assert store.get("gizmo", "shared-id") == {"kind": "gizmo"}
