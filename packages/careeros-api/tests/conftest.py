"""Shared fixtures: an isolated per-test data dir and a TestClient."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from careeros_api import ai_support, app, dependencies


@pytest.fixture(autouse=True)
def isolate_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CAREEROS_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("CAREEROS_ENV", "test")  # allow the dev cipher fallback
    monkeypatch.delenv("CAREEROS_ADMIN_EMAILS", raising=False)
    monkeypatch.delenv("CAREEROS_STRIPE_WEBHOOK_SECRET", raising=False)
    dependencies.get_store.cache_clear()
    yield
    dependencies.get_store.cache_clear()


@pytest.fixture(autouse=True)
def isolate_ai_providers(monkeypatch):
    """Keep the developer's machine out of the test results.

    AI resolution now falls back to locally authenticated agent CLIs, so on a
    machine with `claude` installed every "no AI configured" assertion would
    quietly become "AI configured" — tests would pass or fail depending on
    whose laptop ran them. Both env vars are cleared and the CLI path switched
    off, so a test that wants a provider must say so explicitly.
    """
    monkeypatch.setenv("CAREEROS_LLM_CLI_ENABLED", "0")
    monkeypatch.delenv("CAREEROS_AI_API_KEY", raising=False)
    monkeypatch.delenv("CAREEROS_AI_MODEL", raising=False)
    ai_support.reset_gateway_cache()
    yield
    ai_support.reset_gateway_cache()


@pytest.fixture
def client():
    return TestClient(app)


PASSWORD = "Very-Secure-Password-1!"


@pytest.fixture
def auth_headers(client):
    def _make(email="ada@example.com", full_name="Ada Lovelace"):
        response = client.post(
            "/auth/signup",
            json={"email": email, "password": PASSWORD, "full_name": full_name},
        )
        assert response.status_code == 201, response.text
        return {"Authorization": f"Bearer {response.json()['token']}"}

    return _make
