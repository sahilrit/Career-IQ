"""Shared fixtures: an isolated per-test data dir and a TestClient."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from careeros_api import app, dependencies


@pytest.fixture(autouse=True)
def isolate_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CAREEROS_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("CAREEROS_ADMIN_EMAILS", raising=False)
    monkeypatch.delenv("CAREEROS_STRIPE_WEBHOOK_SECRET", raising=False)
    dependencies.get_store.cache_clear()
    yield
    dependencies.get_store.cache_clear()


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
