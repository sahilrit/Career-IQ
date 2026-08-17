"""Tests for the Google integration endpoints (no real Google calls)."""

from __future__ import annotations

from careeros_api import integrations_google as google


def test_status_unconfigured(client, auth_headers, monkeypatch):
    monkeypatch.delenv("CAREEROS_GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("CAREEROS_GOOGLE_CLIENT_SECRET", raising=False)
    body = client.get("/integrations/google", headers=auth_headers()).json()
    assert body == {"configured": False, "connected": False, "email": None}


def test_auth_url_503_when_unconfigured(client, auth_headers, monkeypatch):
    monkeypatch.delenv("CAREEROS_GOOGLE_CLIENT_ID", raising=False)
    assert client.get("/integrations/google/auth-url", headers=auth_headers()).status_code == 503


def test_build_auth_url_contains_params(monkeypatch):
    monkeypatch.setenv("CAREEROS_GOOGLE_CLIENT_ID", "cid.apps.googleusercontent.com")
    monkeypatch.setenv("CAREEROS_GOOGLE_CLIENT_SECRET", "secret")
    monkeypatch.setenv("CAREEROS_APP_BASE_URL", "https://app.example.com")
    url = google.build_auth_url("state123")
    assert "accounts.google.com" in url
    assert "client_id=cid.apps.googleusercontent.com" in url
    assert "state=state123" in url
    assert "access_type=offline" in url
    assert "settings%2Fgoogle%2Fcallback" in url


def test_connect_stores_and_status_reflects_it(client, auth_headers, monkeypatch):
    monkeypatch.setenv("CAREEROS_GOOGLE_CLIENT_ID", "cid")
    monkeypatch.setenv("CAREEROS_GOOGLE_CLIENT_SECRET", "secret")
    monkeypatch.setattr(
        google, "exchange_code", lambda code: {"refresh_token": "r-123", "access_token": "a-1"}
    )
    monkeypatch.setattr(google, "userinfo_email", lambda token: "me@gmail.com")

    headers = auth_headers()
    connected = client.post("/integrations/google/connect", headers=headers, json={"code": "abc"})
    assert connected.status_code == 200
    assert connected.json() == {"connected": True, "email": "me@gmail.com"}

    status = client.get("/integrations/google", headers=headers).json()
    assert status["connected"] is True
    assert status["email"] == "me@gmail.com"

    assert client.delete("/integrations/google", headers=headers).status_code == 200
    assert client.get("/integrations/google", headers=headers).json()["connected"] is False


def test_connect_without_refresh_token_is_400(client, auth_headers, monkeypatch):
    monkeypatch.setenv("CAREEROS_GOOGLE_CLIENT_ID", "cid")
    monkeypatch.setenv("CAREEROS_GOOGLE_CLIENT_SECRET", "secret")
    monkeypatch.setattr(google, "exchange_code", lambda code: {"access_token": "a-1"})
    response = client.post(
        "/integrations/google/connect", headers=auth_headers(), json={"code": "x"}
    )
    assert response.status_code == 400


def test_gmail_send_requires_connection(client, auth_headers):
    response = client.post(
        "/integrations/gmail/send",
        headers=auth_headers(),
        json={"to": "x@y.com", "subject": "Hi", "body": "Hello"},
    )
    assert response.status_code == 409


def test_integrations_require_auth(client):
    assert client.get("/integrations/google").status_code == 401
