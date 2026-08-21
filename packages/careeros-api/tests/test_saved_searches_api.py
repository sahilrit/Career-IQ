"""Saved searches + new-match digest (search execution is stubbed — no network)."""

from __future__ import annotations

import pytest

from careeros_api import dependencies
from careeros_api.routers import saved_searches
from careeros_career_brain import Application, CareerBrain, CareerBrainRepository, Identity
from careeros_tenancy import TenantScopedDocumentStore


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    # search_for_jobs would hit real providers; stub it to a no-op.
    monkeypatch.setattr(saved_searches, "search_for_jobs", lambda *a, **k: {"discovered": 0})


def _brain_with_apps(client, headers, *apps):
    workspace_id = client.get("/auth/me", headers=headers).json()["workspace_id"]
    scoped = TenantScopedDocumentStore(dependencies.get_store(), workspace_id)
    brain = CareerBrain(identity=Identity(full_name="Sahil", email="s@example.com"))
    brain.applications.extend(apps)
    CareerBrainRepository(scoped).save(brain)


def test_create_list_delete(client, auth_headers):
    headers = auth_headers()
    _brain_with_apps(client, headers)
    created = client.post("/saved-searches", headers=headers, json={"keywords": ["growth", "ppc"]})
    assert created.status_code == 201
    sid = created.json()["id"]
    assert len(client.get("/saved-searches", headers=headers).json()) == 1
    assert client.delete(f"/saved-searches/{sid}", headers=headers).status_code == 200
    assert client.get("/saved-searches", headers=headers).json() == []


def test_empty_keywords_is_422(client, auth_headers):
    headers = auth_headers()
    r = client.post("/saved-searches", headers=headers, json={"keywords": ["  "]})
    assert r.status_code == 422


def test_run_reports_only_new_matches(client, auth_headers):
    headers = auth_headers()
    a = Application(job_title="Growth Lead", company_name="Ramp", match_score=0.9)
    b = Application(job_title="PPC Manager", company_name="Linear", match_score=0.8)
    _brain_with_apps(client, headers, a, b)
    sid = client.post("/saved-searches", headers=headers, json={"keywords": ["growth"]}).json()[
        "id"
    ]

    # First run: both are new, ranked by score.
    first = client.post(f"/saved-searches/{sid}/run", headers=headers, json={}).json()
    assert first["new_count"] == 2
    assert first["new_matches"][0]["job_title"] == "Growth Lead"

    # Second run with nothing added: no new matches.
    second = client.post(f"/saved-searches/{sid}/run", headers=headers, json={}).json()
    assert second["new_count"] == 0


def test_run_needs_a_brain(client, auth_headers):
    headers = auth_headers()
    # saved search can be created only via keywords; but running needs a brain
    sid = client.post("/saved-searches", headers=headers, json={"keywords": ["x"]}).json()["id"]
    r = client.post(f"/saved-searches/{sid}/run", headers=headers, json={})
    assert r.status_code == 404


def test_run_unknown_search_is_404(client, auth_headers):
    headers = auth_headers()
    _brain_with_apps(client, headers)
    r = client.post("/saved-searches/nope/run", headers=headers, json={})
    assert r.status_code == 404


def test_email_not_sent_when_smtp_unconfigured(client, auth_headers):
    headers = auth_headers()
    a = Application(job_title="Growth Lead", company_name="Ramp", match_score=0.9)
    _brain_with_apps(client, headers, a)
    sid = client.post("/saved-searches", headers=headers, json={"keywords": ["growth"]}).json()[
        "id"
    ]
    r = client.post(f"/saved-searches/{sid}/run", headers=headers, json={"send_email": True}).json()
    assert r["new_count"] == 1
    assert r["emailed"] is False  # no SMTP in tests
    assert r["email_configured"] is False


def test_saved_searches_require_auth(client):
    assert client.get("/saved-searches").status_code == 401
