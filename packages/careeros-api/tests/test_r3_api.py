"""Contract tests for the billing, autopilot, and admin endpoints."""

from __future__ import annotations

from careeros_api import dependencies
from careeros_tenancy import TenantScopedDocumentStore


def test_billing_defaults_to_free(client, auth_headers):
    headers = auth_headers()
    body = client.get("/billing", headers=headers).json()
    assert body["current_tier"] == "free"
    tiers = {p["tier"] for p in body["plans"]}
    assert {"free", "pro", "agency"} <= tiers
    free = next(p for p in body["plans"] if p["tier"] == "free")
    assert free["is_current"] is True


def test_billing_upgrade_link_from_env(client, auth_headers, monkeypatch):
    monkeypatch.setenv("CAREEROS_STRIPE_LINK_PRO", "https://buy.stripe.com/pro")
    headers = auth_headers()
    plans = client.get("/billing", headers=headers).json()["plans"]
    pro = next(p for p in plans if p["tier"] == "pro")
    assert pro["checkout_url"] == "https://buy.stripe.com/pro"


def test_billing_requires_auth(client):
    assert client.get("/billing").status_code == 401


def test_autopilot_runs_empty_then_reads_history(client, auth_headers):
    headers = auth_headers()
    assert client.get("/autopilot/runs", headers=headers).json() == []

    # Seed an autopilot_run doc into the account's workspace directly.
    workspace_id = client.get("/auth/me", headers=headers).json()["workspace_id"]
    scoped = TenantScopedDocumentStore(dependencies.get_store(), workspace_id)
    scoped.put(
        "autopilot_run",
        "run-1",
        {
            "id": "run-1",
            "ran_at": "2026-08-17T10:00:00+00:00",
            "discovered": 5,
            "submitted": 2,
            "qualified_total": 3,
            "outcomes": [
                {"job_title": "PMM", "company_name": "Acme", "submitted": True, "reason": "ok"}
            ],
        },
    )
    runs = client.get("/autopilot/runs", headers=headers).json()
    assert len(runs) == 1
    assert runs[0]["submitted"] == 2
    assert runs[0]["outcomes"][0]["job_title"] == "PMM"


def test_admin_denies_non_admin(client, auth_headers):
    headers = auth_headers()
    assert client.get("/admin/overview", headers=headers).status_code == 403


def test_admin_overview_and_activate(client, auth_headers, monkeypatch):
    monkeypatch.setenv("CAREEROS_ADMIN_EMAILS", "ada@example.com")
    headers = auth_headers()  # ada@example.com
    overview = client.get("/admin/overview", headers=headers).json()
    assert overview["accounts"] == 1
    assert overview["mrr"] == 0
    workspace_id = overview["customers"][0]["workspace_id"]

    activated = client.post(
        "/admin/activate", headers=headers, json={"workspace_id": workspace_id, "tier": "agency"}
    ).json()
    assert activated["paying_workspaces"] == 1
    assert activated["mrr"] == 99
    assert activated["customers"][0]["plan"] == "agency"
