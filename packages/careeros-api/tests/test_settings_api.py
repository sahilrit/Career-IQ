"""Contract tests for the AI key settings endpoints (write-only key)."""

from __future__ import annotations


def test_ai_key_round_trip(client, auth_headers):
    headers = auth_headers()
    assert client.get("/settings/ai", headers=headers).json()["has_key"] is False
    put = client.put("/settings/ai", headers=headers, json={"api_key": "sk-ant-api03-abc123456789"})
    assert put.status_code == 200
    assert put.json()["has_key"] is True
    assert client.get("/settings/ai", headers=headers).json()["has_key"] is True
    assert client.delete("/settings/ai", headers=headers).status_code == 200
    assert client.get("/settings/ai", headers=headers).json()["has_key"] is False


def test_get_never_returns_the_key(client, auth_headers):
    headers = auth_headers()
    client.put("/settings/ai", headers=headers, json={"api_key": "sk-ant-secret-value-123"})
    body = client.get("/settings/ai", headers=headers).json()
    assert "sk-ant-secret-value-123" not in str(body)
    assert set(body.keys()) == {"has_key", "model"}


def test_put_rejects_malformed_key(client, auth_headers):
    response = client.put("/settings/ai", headers=auth_headers(), json={"api_key": "nope"})
    assert response.status_code == 422


def test_settings_requires_auth(client):
    assert client.get("/settings/ai").status_code == 401
    assert client.put("/settings/ai", json={"api_key": "sk-ant-x"}).status_code == 401


def test_ai_model_set_updated_and_cleared(client, auth_headers):
    headers = auth_headers()
    free = "meta-llama/llama-3.3-70b-instruct:free"
    put = client.put(
        "/settings/ai", headers=headers, json={"api_key": "sk-or-v1-key1234567890", "model": free}
    )
    assert put.status_code == 200
    assert put.json() == {"has_key": True, "model": free}

    # Update the model without re-entering the key.
    updated = client.put(
        "/settings/ai", headers=headers, json={"api_key": "", "model": "google/gemini:free"}
    )
    assert updated.json() == {"has_key": True, "model": "google/gemini:free"}

    # Blank clears back to the provider default.
    cleared = client.put("/settings/ai", headers=headers, json={"api_key": "", "model": ""})
    assert cleared.json()["model"] == "your provider's default"


def test_model_only_update_needs_a_key_first(client, auth_headers):
    response = client.put(
        "/settings/ai", headers=auth_headers(), json={"api_key": "", "model": "x:free"}
    )
    assert response.status_code == 422


def test_keys_are_workspace_isolated(client, auth_headers):
    headers_a = auth_headers(email="a@example.com", full_name="A")
    headers_b = auth_headers(email="b@example.com", full_name="B")
    client.put("/settings/ai", headers=headers_a, json={"api_key": "sk-ant-a-key-1234567"})
    assert client.get("/settings/ai", headers=headers_a).json()["has_key"] is True
    assert client.get("/settings/ai", headers=headers_b).json()["has_key"] is False
