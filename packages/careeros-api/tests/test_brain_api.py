"""Contract tests for the tenant-scoped brain endpoints, including
isolation between two accounts."""

from __future__ import annotations

from careeros_api import dependencies
from careeros_career_brain import CareerBrain, CareerBrainRepository, Identity
from careeros_tenancy import TenantScopedDocumentStore


def _seed_brain(headers, client, *, full_name, email):
    workspace_id = client.get("/auth/me", headers=headers).json()["workspace_id"]
    scoped = TenantScopedDocumentStore(dependencies.get_store(), workspace_id)
    CareerBrainRepository(scoped).save(
        CareerBrain(identity=Identity(full_name=full_name, email=email))
    )


def test_brain_404_when_empty(client, auth_headers):
    headers = auth_headers()
    assert client.get("/brain", headers=headers).status_code == 404


def test_brain_returns_seeded_brain(client, auth_headers):
    headers = auth_headers()
    _seed_brain(headers, client, full_name="Ada Lovelace", email="ada@example.com")
    response = client.get("/brain", headers=headers)
    assert response.status_code == 200
    assert response.json()["identity"]["full_name"] == "Ada Lovelace"


def test_brain_requires_auth(client):
    assert client.get("/brain").status_code == 401


def test_two_accounts_are_isolated(client, auth_headers):
    headers_a = auth_headers(email="a@example.com", full_name="User A")
    headers_b = auth_headers(email="b@example.com", full_name="User B")
    _seed_brain(headers_a, client, full_name="User A", email="a@example.com")

    assert client.get("/brain", headers=headers_a).status_code == 200
    # B never created a brain and cannot see A's.
    assert client.get("/brain", headers=headers_b).status_code == 404
