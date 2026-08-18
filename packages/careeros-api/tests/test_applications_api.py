"""Application pipeline tracking: list, board, status transitions, notes."""

from __future__ import annotations

from careeros_api import dependencies
from careeros_career_brain import Application, CareerBrain, CareerBrainRepository, Identity
from careeros_tenancy import TenantScopedDocumentStore


def _seed_application(headers, client, **kwargs) -> str:
    workspace_id = client.get("/auth/me", headers=headers).json()["workspace_id"]
    scoped = TenantScopedDocumentStore(dependencies.get_store(), workspace_id)
    repo = CareerBrainRepository(scoped)
    brain = CareerBrain(identity=Identity(full_name="Sahil", email="s@example.com"))
    application = Application(job_title="Growth Lead", company_name="Ramp", **kwargs)
    brain.applications.append(application)
    repo.save(brain)
    return application.id


def test_list_empty_without_brain(client, auth_headers):
    assert client.get("/applications", headers=auth_headers()).json() == []


def test_list_and_board(client, auth_headers):
    headers = auth_headers()
    _seed_application(headers, client)
    listed = client.get("/applications", headers=headers).json()
    assert len(listed) == 1 and listed[0]["job_title"] == "Growth Lead"

    board = client.get("/applications/board", headers=headers).json()
    assert board["total"] == 1
    assert board["counts"]["discovered"] == 1
    assert board["columns"]["discovered"][0]["company_name"] == "Ramp"


def test_advance_status_follows_state_machine(client, auth_headers):
    headers = auth_headers()
    app_id = _seed_application(headers, client)
    # discovered -> qualified -> applied is allowed
    r1 = client.post(f"/applications/{app_id}/status", headers=headers, json={"to": "qualified"})
    assert r1.status_code == 200 and r1.json()["status"] == "qualified"
    r2 = client.post(
        f"/applications/{app_id}/status",
        headers=headers,
        json={"to": "applied", "note": "submitted via careers page"},
    )
    assert r2.status_code == 200 and r2.json()["status"] == "applied"
    history = r2.json()["history"]
    assert history[-1]["note"] == "submitted via careers page"


def test_illegal_transition_is_409(client, auth_headers):
    headers = auth_headers()
    app_id = _seed_application(headers, client)
    # discovered -> offer is not allowed
    r = client.post(f"/applications/{app_id}/status", headers=headers, json={"to": "offer"})
    assert r.status_code == 409


def test_unknown_status_is_422(client, auth_headers):
    headers = auth_headers()
    app_id = _seed_application(headers, client)
    r = client.post(f"/applications/{app_id}/status", headers=headers, json={"to": "hired"})
    assert r.status_code == 422


def test_unknown_application_is_404(client, auth_headers):
    headers = auth_headers()
    _seed_application(headers, client)
    r = client.post("/applications/nope/status", headers=headers, json={"to": "qualified"})
    assert r.status_code == 404


def test_update_notes(client, auth_headers):
    headers = auth_headers()
    app_id = _seed_application(headers, client)
    r = client.patch(
        f"/applications/{app_id}", headers=headers, json={"notes": "referred by Priya"}
    )
    assert r.status_code == 200 and r.json()["notes"] == "referred by Priya"


def test_applications_require_auth(client):
    assert client.get("/applications").status_code == 401


def test_tenancy_isolation(client, auth_headers):
    headers_a = auth_headers(email="a@example.com", full_name="A")
    headers_b = auth_headers(email="b@example.com", full_name="B")
    app_id = _seed_application(headers_a, client)
    # B cannot see or mutate A's application
    assert client.get("/applications", headers=headers_b).json() == []
    assert (
        client.post(
            f"/applications/{app_id}/status", headers=headers_b, json={"to": "qualified"}
        ).status_code
        == 404
    )


# --- ATS keyword gap per match (roadmap #2) ----------------------------------


def test_keyword_gap_matched_and_missing(client, auth_headers):
    from careeros_career_brain.models import Skill
    from careeros_job_discovery import JobPostingRepository
    from careeros_job_providers import JobPosting

    headers = auth_headers()
    workspace_id = client.get("/auth/me", headers=headers).json()["workspace_id"]
    scoped = TenantScopedDocumentStore(dependencies.get_store(), workspace_id)
    brain = CareerBrain(
        identity=Identity(full_name="Sahil", email="s@example.com"),
        skills=[Skill(name="Meta Ads"), Skill(name="SQL")],
    )
    posting = JobPosting(
        source_provider="x",
        external_id="1",
        title="Growth Marketer",
        company_name="Ramp",
        url="https://jobs/1",
        tags=["Meta Ads", "Google Ads", "SQL"],
    )
    JobPostingRepository(scoped).save(posting)
    application = Application(
        job_title="Growth Marketer", company_name="Ramp", job_url="https://jobs/1"
    )
    brain.applications.append(application)
    CareerBrainRepository(scoped).save(brain)

    body = client.get(f"/applications/{application.id}/gap", headers=headers).json()
    assert body["available"] is True
    assert set(body["matched_skills"]) == {"Meta Ads", "SQL"}
    assert body["missing_keywords"] == ["Google Ads"]


def test_keyword_gap_unavailable_when_posting_not_cached(client, auth_headers):
    headers = auth_headers()
    app_id = _seed_application(headers, client, job_url="https://uncached/9")
    body = client.get(f"/applications/{app_id}/gap", headers=headers).json()
    assert body["available"] is False


# --- Follow-up reminders (roadmap #4) ----------------------------------------


def test_set_and_clear_follow_up(client, auth_headers):
    headers = auth_headers()
    app_id = _seed_application(headers, client)

    r = client.patch(
        f"/applications/{app_id}/follow-up", headers=headers, json={"date": "2099-01-15"}
    )
    assert r.status_code == 200
    assert r.json()["application"]["follow_up_date"] == "2099-01-15"

    ups = client.get("/applications/follow-ups", headers=headers).json()
    assert len(ups) == 1
    assert ups[0]["due"] is False and ups[0]["days_until"] > 0

    # clearing removes it from the list
    client.patch(f"/applications/{app_id}/follow-up", headers=headers, json={"date": None})
    assert client.get("/applications/follow-ups", headers=headers).json() == []


def test_follow_up_due_flag(client, auth_headers):
    headers = auth_headers()
    app_id = _seed_application(headers, client)
    client.patch(f"/applications/{app_id}/follow-up", headers=headers, json={"date": "2000-01-01"})
    ups = client.get("/applications/follow-ups", headers=headers).json()
    assert ups[0]["due"] is True


def test_follow_up_bad_date_is_422(client, auth_headers):
    headers = auth_headers()
    app_id = _seed_application(headers, client)
    r = client.patch(f"/applications/{app_id}/follow-up", headers=headers, json={"date": "nope"})
    assert r.status_code == 422


def test_follow_up_calendar_needs_google(client, auth_headers):
    headers = auth_headers()
    app_id = _seed_application(headers, client)
    r = client.patch(
        f"/applications/{app_id}/follow-up",
        headers=headers,
        json={"date": "2099-01-15", "add_to_calendar": True},
    )
    assert r.status_code == 200
    # follow-up is still set; calendar gracefully reports it needs a connection
    assert r.json()["application"]["follow_up_date"] == "2099-01-15"
    assert r.json()["calendar"]["created"] is False
    assert "Google" in r.json()["calendar"]["reason"]
