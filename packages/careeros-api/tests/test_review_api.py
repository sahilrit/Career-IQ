"""Review queue API — prepared (captcha-gated) applications for a human."""

from __future__ import annotations

from careeros_api import dependencies
from careeros_tenancy import TenantScopedDocumentStore


def _seed(headers, client, prepared_id="p1", status="pending"):
    workspace_id = client.get("/auth/me", headers=headers).json()["workspace_id"]
    scoped = TenantScopedDocumentStore(dependencies.get_store(), workspace_id)
    scoped.put(
        "prepared_application",
        prepared_id,
        {
            "id": prepared_id,
            "application_id": "a1",
            "job_title": "PPC Specialist",
            "company_name": "Creatio",
            "apply_url": "https://jobs.eu.lever.co/creatio/abc/apply",
            "cover_letter": "Dear hiring team, ...",
            "match_score": 0.82,
            "prepared_at": "2026-08-24T12:00:00+00:00",
            "status": status,
        },
    )


def test_lists_only_pending_prepared(client, auth_headers):
    headers = auth_headers()
    _seed(headers, client, "p1", "pending")
    _seed(headers, client, "p2", "submitted")  # already done -> excluded

    body = client.get("/review/prepared", headers=headers).json()
    assert [item["id"] for item in body] == ["p1"]
    assert body[0]["job_title"] == "PPC Specialist"
    assert body[0]["apply_url"].startswith("https://jobs.eu.lever.co")
    assert body[0]["cover_letter"].startswith("Dear hiring team")


def test_mark_submitted_drops_it_from_the_queue(client, auth_headers):
    headers = auth_headers()
    _seed(headers, client)
    r = client.patch("/review/prepared/p1", headers=headers, json={"status": "submitted"})
    assert r.status_code == 200
    assert client.get("/review/prepared", headers=headers).json() == []


def test_dismiss_also_drops_it(client, auth_headers):
    headers = auth_headers()
    _seed(headers, client)
    assert (
        client.patch(
            "/review/prepared/p1", headers=headers, json={"status": "dismissed"}
        ).status_code
        == 200
    )
    assert client.get("/review/prepared", headers=headers).json() == []


def test_bad_status_is_422(client, auth_headers):
    headers = auth_headers()
    _seed(headers, client)
    assert (
        client.patch("/review/prepared/p1", headers=headers, json={"status": "nope"}).status_code
        == 422
    )


def test_unknown_id_is_404(client, auth_headers):
    headers = auth_headers()
    assert (
        client.patch(
            "/review/prepared/nope", headers=headers, json={"status": "submitted"}
        ).status_code
        == 404
    )


def test_review_requires_auth(client):
    assert client.get("/review/prepared").status_code == 401
