"""Contract tests for the opportunity endpoints. The provider search is
patched so tests never hit the real network."""

from __future__ import annotations

import types

from careeros_api.routers import opportunities


def _create_brain(client, headers):
    client.post("/brain", headers=headers, json={"full_name": "Ada", "email": "ada@example.com"})


def test_search_requires_a_brain(client, auth_headers):
    headers = auth_headers()
    response = client.post("/opportunities/search", headers=headers, json={"keywords": ["ppc"]})
    assert response.status_code == 404


def test_search_returns_summary(client, auth_headers, monkeypatch):
    headers = auth_headers()
    _create_brain(client, headers)

    def fake_search(store, identity_id, *, keywords, remote_only, limit):
        assert keywords == ["performance marketing"]
        return {"discovered": 12, "qualified": 4}

    monkeypatch.setattr(opportunities, "search_for_jobs", fake_search)
    response = client.post(
        "/opportunities/search",
        headers=headers,
        json={"keywords": ["performance marketing"], "remote_only": True, "limit": 50},
    )
    assert response.status_code == 200
    assert response.json() == {"discovered": 12, "qualified": 4}


def test_search_requires_auth(client):
    assert client.post("/opportunities/search", json={"keywords": []}).status_code == 401


def test_generate_returns_package(client, auth_headers, monkeypatch):
    headers = auth_headers()
    _create_brain(client, headers)

    fake_package = types.SimpleNamespace(
        resume_text="RESUME BODY", cover_letter="COVER LETTER BODY"
    )
    monkeypatch.setattr(opportunities, "generate_application_for_job", lambda *a, **k: fake_package)
    response = client.post(
        "/opportunities/generate", headers=headers, json={"job_url": "https://x/job/1"}
    )
    assert response.status_code == 200
    assert response.json()["resume_text"] == "RESUME BODY"
    assert response.json()["cover_letter"] == "COVER LETTER BODY"


def test_generate_missing_posting_is_404(client, auth_headers, monkeypatch):
    headers = auth_headers()
    _create_brain(client, headers)
    monkeypatch.setattr(opportunities, "generate_application_for_job", lambda *a, **k: None)
    response = client.post(
        "/opportunities/generate", headers=headers, json={"job_url": "https://x/gone"}
    )
    assert response.status_code == 404
