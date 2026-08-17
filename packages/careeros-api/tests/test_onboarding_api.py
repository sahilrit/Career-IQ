"""Contract tests for the onboarding checklist endpoint."""

from __future__ import annotations


def test_onboarding_requires_auth(client):
    assert client.get("/onboarding").status_code == 401


def test_onboarding_before_brain(client, auth_headers):
    body = client.get("/onboarding", headers=auth_headers()).json()
    assert body["complete"] is False
    keys = {step["key"] for step in body["steps"]}
    assert {"brain", "profile", "ai", "search"} <= keys
    brain_step = next(step for step in body["steps"] if step["key"] == "brain")
    assert brain_step["done"] is False


def test_onboarding_marks_brain_done(client, auth_headers):
    headers = auth_headers()
    client.post("/brain", headers=headers, json={"full_name": "Ada", "email": "ada@example.com"})
    body = client.get("/onboarding", headers=headers).json()
    brain_step = next(step for step in body["steps"] if step["key"] == "brain")
    assert brain_step["done"] is True
    # No skills/AI/search yet → still incomplete.
    assert body["complete"] is False
