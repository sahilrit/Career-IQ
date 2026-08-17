"""Contract tests for the opportunity endpoints. The provider search is
patched so tests never hit the real network."""

from __future__ import annotations

import types

from careeros_ai import AIError
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
    # No AI key configured → template path.
    assert response.json()["ai_used"] is False


def test_generate_missing_posting_is_404(client, auth_headers, monkeypatch):
    headers = auth_headers()
    _create_brain(client, headers)
    monkeypatch.setattr(opportunities, "generate_application_for_job", lambda *a, **k: None)
    response = client.post(
        "/opportunities/generate", headers=headers, json={"job_url": "https://x/gone"}
    )
    assert response.status_code == 404


def test_generate_reports_ai_used_when_key_present(client, auth_headers, monkeypatch):
    headers = auth_headers()
    _create_brain(client, headers)
    client.put("/settings/ai", headers=headers, json={"api_key": "sk-ant-api03-key-1234567"})

    fake_package = types.SimpleNamespace(resume_text="R", cover_letter="AI COVER")
    monkeypatch.setattr(opportunities, "generate_application_for_job", lambda *a, **k: fake_package)
    response = client.post(
        "/opportunities/generate", headers=headers, json={"job_url": "https://x/job/1"}
    )
    assert response.status_code == 200
    assert response.json()["ai_used"] is True


def test_generate_falls_back_to_template_on_ai_error(client, auth_headers, monkeypatch):
    headers = auth_headers()
    _create_brain(client, headers)
    client.put("/settings/ai", headers=headers, json={"api_key": "sk-ant-api03-key-1234567"})

    template_package = types.SimpleNamespace(resume_text="R", cover_letter="TEMPLATE COVER")

    def fake_generate(store, identity_id, job_url, *, cover_letter_generator=None, **kwargs):
        if cover_letter_generator is not None:
            raise AIError("boom")
        return template_package

    monkeypatch.setattr(opportunities, "generate_application_for_job", fake_generate)
    response = client.post(
        "/opportunities/generate", headers=headers, json={"job_url": "https://x/job/1"}
    )
    assert response.status_code == 200
    assert response.json()["cover_letter"] == "TEMPLATE COVER"
    assert response.json()["ai_used"] is False
