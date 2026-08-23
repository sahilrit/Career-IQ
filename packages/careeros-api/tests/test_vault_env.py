"""The secret cipher must hard-fail in production without a key, and use the
configured key when present."""

from __future__ import annotations

import pytest

from careeros_api import vault_support


def test_production_without_key_raises(monkeypatch):
    monkeypatch.setenv("CAREEROS_ENV", "production")
    monkeypatch.delenv("CAREEROS_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError):
        vault_support.cipher()


def test_configured_key_roundtrips(monkeypatch):
    monkeypatch.setenv("CAREEROS_ENV", "production")
    monkeypatch.setenv("CAREEROS_SECRET_KEY", "a-real-long-random-secret-value")
    cipher = vault_support.cipher()
    token = cipher.encrypt("sk-ant-SECRET")
    assert token != "sk-ant-SECRET"
    assert cipher.decrypt(token) == "sk-ant-SECRET"


def test_non_strict_env_falls_back(monkeypatch):
    monkeypatch.setenv("CAREEROS_ENV", "test")
    monkeypatch.delenv("CAREEROS_SECRET_KEY", raising=False)
    # warns + uses fallback rather than raising, so local/dev keeps working
    assert vault_support.cipher() is not None
