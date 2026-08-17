"""Contract tests for the offers, network, and freelance endpoints."""

from __future__ import annotations

# -- offers -----------------------------------------------------------------


def test_offers_empty_then_ranked(client, auth_headers):
    headers = auth_headers()
    assert client.get("/offers", headers=headers).json() == []
    client.post(
        "/offers",
        headers=headers,
        json={"company_name": "Acme", "job_title": "PMM", "base_salary": 120000},
    )
    client.post(
        "/offers",
        headers=headers,
        json={"company_name": "Globex", "job_title": "PMM", "base_salary": 90000},
    )
    ranked = client.get("/offers", headers=headers).json()
    assert len(ranked) == 2
    # Higher opportunity value ranks first.
    assert ranked[0]["opportunity_value"] >= ranked[1]["opportunity_value"]


def test_offers_require_auth(client):
    assert client.get("/offers").status_code == 401


# -- network ----------------------------------------------------------------


def test_add_and_list_contacts(client, auth_headers):
    headers = auth_headers()
    created = client.post(
        "/contacts",
        headers=headers,
        json={"name": "Jane Doe", "role": "recruiter", "organization_name": "Acme"},
    )
    assert created.status_code == 201
    assert created.json()["name"] == "Jane Doe"
    listed = client.get("/contacts", headers=headers).json()
    assert [c["name"] for c in listed] == ["Jane Doe"]


def test_add_contact_bad_role_is_422(client, auth_headers):
    headers = auth_headers()
    response = client.post("/contacts", headers=headers, json={"name": "X", "role": "not-a-role"})
    assert response.status_code == 422


# -- freelance --------------------------------------------------------------


def test_add_prospect_normalizes_url_and_lists(client, auth_headers):
    headers = auth_headers()
    created = client.post(
        "/freelance/prospects",
        headers=headers,
        json={"name": "Acme DTC", "website": "acme.com", "industry": "ecommerce"},
    )
    assert created.status_code == 201
    assert created.json()["website"] == "https://acme.com"
    assert created.json()["stage"] == "discovery"
    listed = client.get("/freelance/prospects", headers=headers).json()
    assert [p["name"] for p in listed] == ["Acme DTC"]


def test_freelance_requires_auth(client):
    assert client.get("/freelance/prospects").status_code == 401
