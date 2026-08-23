"""Per-IP rate limiting on abuse-prone auth endpoints (enforced outside dev)."""

from __future__ import annotations


def test_signup_is_rate_limited_when_enforced(client, monkeypatch):
    monkeypatch.setenv("CAREEROS_ENV", "production")  # turn enforcement on
    # 5 signups / 60s allowed; the middleware counts every POST (even rejected).
    for i in range(5):
        client.post(
            "/auth/signup",
            json={"email": f"rl{i}@x.com", "password": "weak", "full_name": "X"},
        )
    blocked = client.post(
        "/auth/signup",
        json={"email": "rl9@x.com", "password": "weak", "full_name": "X"},
    )
    assert blocked.status_code == 429
    assert "Too many requests" in blocked.json()["detail"]
    assert blocked.headers.get("Retry-After")


def test_not_enforced_in_test_env(client):
    # Default test env: no limiting, so many signups succeed/normal-error.
    codes = {
        client.post(
            "/auth/signup",
            json={
                "email": f"free{i}@x.com",
                "password": "Very-Secure-Password-1!",
                "full_name": "X",
            },
        ).status_code
        for i in range(8)
    }
    assert 429 not in codes
