"""Contract tests for the auth endpoints."""

from __future__ import annotations

WEAK = "short"
STRONG = "Very-Secure-Password-1!"


def test_signup_returns_a_bearer_token(client):
    response = client.post(
        "/auth/signup",
        json={"email": "ada@example.com", "password": STRONG, "full_name": "Ada"},
    )
    assert response.status_code == 201
    assert response.json()["token"]


def test_signup_duplicate_is_409(client):
    body = {"email": "ada@example.com", "password": STRONG, "full_name": "Ada"}
    client.post("/auth/signup", json=body)
    assert client.post("/auth/signup", json=body).status_code == 409


def test_signup_weak_password_is_422(client):
    response = client.post(
        "/auth/signup",
        json={"email": "weak@example.com", "password": WEAK, "full_name": "Weak"},
    )
    assert response.status_code == 422


def test_login_and_me(client, auth_headers):
    auth_headers()  # signs up ada
    login = client.post("/auth/login", json={"email": "ada@example.com", "password": STRONG})
    assert login.status_code == 200
    token = login.json()["token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "ada@example.com"
    assert me.json()["role"] == "owner"


def test_login_wrong_password_is_401(client, auth_headers):
    auth_headers()
    response = client.post("/auth/login", json={"email": "ada@example.com", "password": "nope"})
    assert response.status_code == 401


def test_me_without_token_is_401(client):
    assert client.get("/auth/me").status_code == 401


def test_me_with_garbage_token_is_401(client):
    assert client.get("/auth/me", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_reset_request_is_always_200(client):
    response = client.post("/auth/reset/request", json={"email": "nobody@example.com"})
    assert response.status_code == 200


def test_admin_flag_reflects_env(client, auth_headers, monkeypatch):
    monkeypatch.setenv("CAREEROS_ADMIN_EMAILS", "ada@example.com")
    headers = auth_headers()
    assert client.get("/auth/me", headers=headers).json()["is_admin"] is True


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
