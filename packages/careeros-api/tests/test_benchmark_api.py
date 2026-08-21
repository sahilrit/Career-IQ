"""Compensation benchmark — transparent estimate, honest about its limits."""

from __future__ import annotations

from careeros_api import dependencies
from careeros_career_brain import CareerBrain, CareerBrainRepository, Identity
from careeros_career_brain.models import Experience, Preferences
from careeros_tenancy import TenantScopedDocumentStore


def _seed_brain(client, headers, **prefs):
    workspace_id = client.get("/auth/me", headers=headers).json()["workspace_id"]
    scoped = TenantScopedDocumentStore(dependencies.get_store(), workspace_id)
    brain = CareerBrain(
        identity=Identity(full_name="Sahil", email="s@example.com"),
        preferences=Preferences(**prefs),
        experiences=[
            Experience(
                company_name="Acme",
                title="Marketer",
                start_date="2019-01-01",
                end_date="2025-01-01",
            )
        ],  # ~6 yrs -> senior
    )
    CareerBrainRepository(scoped).save(brain)


def test_benchmark_anchored_uses_your_number(client, auth_headers):
    headers = auth_headers()
    _seed_brain(client, headers, salary_currency="INR", min_salary=1500000)
    r = client.post(
        "/offers/benchmark",
        headers=headers,
        json={"role": "Growth Marketer", "anchor_salary": 2000000},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["currency"] == "INR"
    assert body["mid"] == 2000000
    assert body["low"] < body["mid"] < body["high"]
    assert body["suggested_ask"] >= body["high"]
    assert "not financial advice" in body["disclaimer"]
    assert "anchor" in body["confidence"].lower() or "grounded" in body["confidence"].lower()


def test_benchmark_infers_seniority_from_experience(client, auth_headers):
    headers = auth_headers()
    _seed_brain(client, headers)  # ~6 yrs -> senior
    body = client.post(
        "/offers/benchmark", headers=headers, json={"role": "Software Engineer"}
    ).json()
    assert body["seniority"] == "senior"
    assert body["role_family"] in ("software", "engineer")
    assert body["currency"] == "USD"  # no anchor -> labelled USD estimate


def test_benchmark_respects_min_salary_floor(client, auth_headers):
    headers = auth_headers()
    _seed_brain(client, headers, min_salary=999999999)
    body = client.post("/offers/benchmark", headers=headers, json={"role": "Analyst"}).json()
    assert body["suggested_ask"] == 999999999  # never suggest below your stated minimum


def test_benchmark_requires_role(client, auth_headers):
    r = client.post("/offers/benchmark", headers=auth_headers(), json={})
    assert r.status_code == 422


def test_benchmark_requires_auth(client):
    assert client.post("/offers/benchmark", json={"role": "x"}).status_code == 401
