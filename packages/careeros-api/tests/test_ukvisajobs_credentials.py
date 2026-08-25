"""Tests for the encrypted UK Visa Jobs credential round-trip, following the
same pattern as test_ai_support.py — a real vault via a real (tmp) store,
no mocking."""

from careeros_api.ukvisajobs_credentials import (
    credentials,
    delete_credentials,
    has_credentials,
    store_credentials,
)
from careeros_common import open_store


def test_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("CAREEROS_DATA_DIR", str(tmp_path))
    store = open_store()

    assert has_credentials(store, "ws1") is False
    assert credentials(store, "ws1") is None

    store_credentials(store, "ws1", "ada@example.com", "hunter2")
    assert has_credentials(store, "ws1") is True
    assert credentials(store, "ws1") == ("ada@example.com", "hunter2")

    delete_credentials(store, "ws1")
    assert has_credentials(store, "ws1") is False
    assert credentials(store, "ws1") is None


def test_credentials_are_workspace_isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("CAREEROS_DATA_DIR", str(tmp_path))
    store = open_store()
    store_credentials(store, "ws1", "ada@example.com", "hunter2")
    assert has_credentials(store, "ws1") is True
    assert has_credentials(store, "ws2") is False


def test_a_stored_password_is_not_stored_in_plaintext(tmp_path, monkeypatch):
    monkeypatch.setenv("CAREEROS_DATA_DIR", str(tmp_path))
    store = open_store()
    store_credentials(store, "ws1", "ada@example.com", "very-secret-password")

    # Read the raw document store row directly — the password must not
    # appear anywhere in it unencrypted.
    raw = store.get_or_none("encrypted_secret", "ws1:ukvisajobs")
    assert raw is not None
    assert "very-secret-password" not in str(raw)
