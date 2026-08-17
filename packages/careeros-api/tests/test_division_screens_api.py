"""Contract tests for the 7 division screens surfaced in the React app:
interview, personal-brand, clients, ceo, learning, finance, career-intel."""

from __future__ import annotations


def _brain(client, headers):
    client.post("/brain", headers=headers, json={"full_name": "Ada", "email": "ada@example.com"})


# --- Interview ---------------------------------------------------------------


def test_interview_prep_needs_a_brain(client, auth_headers):
    response = client.post(
        "/interview/prep",
        headers=auth_headers(),
        json={"job_title": "PPC Manager", "company_name": "Acme"},
    )
    assert response.status_code == 404


def test_interview_prep_returns_questions_and_briefing(client, auth_headers):
    headers = auth_headers()
    _brain(client, headers)
    response = client.post(
        "/interview/prep",
        headers=headers,
        json={"job_title": "PPC Manager", "company_name": "Acme", "job_description": "run ads"},
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"questions", "briefing", "briefing_text"}
    assert "role_specific" in body["questions"]


def test_interview_requires_auth(client):
    assert (
        client.post("/interview/prep", json={"job_title": "x", "company_name": "y"}).status_code
        == 401
    )


# --- Personal Brand ----------------------------------------------------------


def test_personal_brand_projects_empty_without_projects(client, auth_headers):
    headers = auth_headers()
    _brain(client, headers)
    response = client.get("/personal-brand/projects", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


def test_personal_brand_generate_unknown_project_is_404(client, auth_headers):
    headers = auth_headers()
    _brain(client, headers)
    response = client.post("/personal-brand/generate", headers=headers, json={"project_id": "nope"})
    assert response.status_code == 404


# --- Clients (Client Success) ------------------------------------------------


def test_clients_full_flow(client, auth_headers):
    headers = auth_headers()
    assert client.get("/clients", headers=headers).json() == []

    created = client.post("/clients", headers=headers, json={"name": "Acme Shop"})
    assert created.status_code == 201
    client_id = created.json()["id"]

    contract = client.post(
        "/clients/contracts",
        headers=headers,
        json={
            "client_id": client_id,
            "title": "Retainer",
            "rate": 2000,
            "start_date": "2026-08-01",
        },
    )
    assert contract.status_code == 201
    contract_id = contract.json()["id"]

    invoice = client.post(
        "/clients/invoices",
        headers=headers,
        json={"contract_id": contract_id, "amount": 500, "due_date": "2026-09-01"},
    )
    assert invoice.status_code == 201

    listed = client.get("/clients", headers=headers).json()
    assert listed[0]["name"] == "Acme Shop"
    assert listed[0]["contracts"][0]["outstanding"] == 500


def test_clients_bad_date_is_422(client, auth_headers):
    headers = auth_headers()
    created = client.post("/clients", headers=headers, json={"name": "X"})
    response = client.post(
        "/clients/contracts",
        headers=headers,
        json={"client_id": created.json()["id"], "title": "T", "start_date": "nope"},
    )
    assert response.status_code == 422


# --- CEO Agent ---------------------------------------------------------------


def test_ceo_record_compute_and_overview(client, auth_headers):
    headers = auth_headers()
    assert client.get("/ceo", headers=headers).json() == {"latest": None, "history": []}
    assert (
        client.post(
            "/ceo/performance",
            headers=headers,
            json={"category": "freelance", "metric_name": "offers", "value": 3},
        ).status_code
        == 201
    )
    computed = client.post("/ceo/compute", headers=headers)
    assert computed.status_code == 200
    assert "allocations" in computed.json()
    assert client.get("/ceo", headers=headers).json()["latest"] is not None


def test_ceo_bad_category_is_422(client, auth_headers):
    response = client.post(
        "/ceo/performance",
        headers=auth_headers(),
        json={"category": "nope", "metric_name": "m", "value": 1},
    )
    assert response.status_code == 422


# --- Learning Lab ------------------------------------------------------------


def test_learning_experiment_variant_outcome_flow(client, auth_headers):
    headers = auth_headers()
    assert client.get("/learning", headers=headers).json() == []

    exp = client.post(
        "/learning/experiments",
        headers=headers,
        json={"experiment_type": "email", "name": "Cold open"},
    )
    assert exp.status_code == 201
    exp_id = exp.json()["id"]

    variant = client.post(
        "/learning/variants", headers=headers, json={"experiment_id": exp_id, "label": "A"}
    )
    assert variant.status_code == 201
    variant_id = variant.json()["id"]

    assert (
        client.post(
            "/learning/outcomes",
            headers=headers,
            json={"variant_id": variant_id, "outcome_type": "sent"},
        ).status_code
        == 201
    )

    board = client.get("/learning", headers=headers).json()
    assert board[0]["variants"][0]["sent"] == 1


def test_learning_bad_type_is_422(client, auth_headers):
    response = client.post(
        "/learning/experiments",
        headers=auth_headers(),
        json={"experiment_type": "nope", "name": "x"},
    )
    assert response.status_code == 422


# --- Finance -----------------------------------------------------------------


def test_finance_add_and_total(client, auth_headers):
    headers = auth_headers()
    assert client.get("/finance/income", headers=headers).json()["total"] == 0
    added = client.post(
        "/finance/income",
        headers=headers,
        json={
            "source": "freelance",
            "source_name": "Acme",
            "amount": 1500,
            "received_date": "2026-08-10",
        },
    )
    assert added.status_code == 201
    assert client.get("/finance/income", headers=headers).json()["total"] == 1500


def test_finance_bad_source_is_422(client, auth_headers):
    response = client.post(
        "/finance/income",
        headers=auth_headers(),
        json={"source": "nope", "source_name": "x", "amount": 1, "received_date": "2026-08-10"},
    )
    assert response.status_code == 422


# --- Career Intel ------------------------------------------------------------


def test_career_intel_signal_and_overview(client, auth_headers):
    headers = auth_headers()
    overview = client.get("/career-intel", headers=headers)
    assert overview.status_code == 200
    assert "direction_summary" in overview.json()
    assert (
        client.post(
            "/career-intel/signals",
            headers=headers,
            json={"category": "role", "subject": "Growth Lead", "score": 5},
        ).status_code
        == 201
    )


def test_career_intel_bad_category_is_422(client, auth_headers):
    response = client.post(
        "/career-intel/signals",
        headers=auth_headers(),
        json={"category": "nope", "subject": "x", "score": 1},
    )
    assert response.status_code == 422


# --- Regression: interview briefing must honour the saved min_salary ----------


def test_interview_briefing_uses_saved_min_salary(client, auth_headers):
    headers = auth_headers()
    _brain(client, headers)
    client.patch("/brain/preferences", headers=headers, json={"min_salary": 140000})
    response = client.post(
        "/interview/prep",
        headers=headers,
        json={"job_title": "Growth Lead", "company_name": "Acme"},
    )
    assert response.status_code == 200
    strategy = response.json()["briefing"]["compensation_strategy"]
    assert "140,000" in strategy  # anchors on the user's real minimum, not "none set"
