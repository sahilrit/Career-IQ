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


def test_create_brain_then_get(client, auth_headers):
    headers = auth_headers()
    created = client.post(
        "/brain", headers=headers, json={"full_name": "Ada Lovelace", "email": "ada@example.com"}
    )
    assert created.status_code == 201
    assert created.json()["identity"]["full_name"] == "Ada Lovelace"
    assert client.get("/brain", headers=headers).status_code == 200


def test_create_brain_twice_is_409(client, auth_headers):
    headers = auth_headers()
    body = {"full_name": "Ada", "email": "ada@example.com"}
    client.post("/brain", headers=headers, json=body)
    assert client.post("/brain", headers=headers, json=body).status_code == 409


def test_update_summary(client, auth_headers):
    headers = auth_headers()
    client.post("/brain", headers=headers, json={"full_name": "Ada", "email": "ada@example.com"})
    response = client.patch("/brain/summary", headers=headers, json={"summary": "4+ years in ML"})
    assert response.status_code == 200
    assert response.json()["identity"]["summary"] == "4+ years in ML"


def test_add_skill(client, auth_headers):
    headers = auth_headers()
    client.post("/brain", headers=headers, json={"full_name": "Ada", "email": "ada@example.com"})
    response = client.post("/brain/skills", headers=headers, json={"name": "Meta Ads"})
    assert response.status_code == 201
    assert any(s["name"] == "Meta Ads" for s in response.json()["skills"])


def test_add_experience_parses_dates(client, auth_headers):
    headers = auth_headers()
    client.post("/brain", headers=headers, json={"full_name": "Ada", "email": "ada@example.com"})
    response = client.post(
        "/brain/experience",
        headers=headers,
        json={"company_name": "Acme", "title": "PPC Manager", "start_date": "2024-05-01"},
    )
    assert response.status_code == 201
    assert response.json()["experiences"][0]["company_name"] == "Acme"


def test_add_experience_bad_date_is_422(client, auth_headers):
    headers = auth_headers()
    client.post("/brain", headers=headers, json={"full_name": "Ada", "email": "ada@example.com"})
    response = client.post(
        "/brain/experience",
        headers=headers,
        json={"company_name": "Acme", "title": "PPC", "start_date": "not-a-date"},
    )
    assert response.status_code == 422


def test_writes_require_auth(client):
    assert client.post("/brain", json={"full_name": "x", "email": "y@z.com"}).status_code == 401
    assert client.post("/brain/skills", json={"name": "x"}).status_code == 401


def _resume_pdf_bytes() -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for line in [
        "Ada Lovelace",
        "Performance Marketer",
        "ada@example.com",
        "+1 555 123 4567",
        "",
        "Professional Summary",
        "Growth marketer with 6 years scaling paid acquisition.",
        "",
        "Skills",
        "Meta Ads, Google Ads, A/B Testing, SQL",
    ]:
        pdf.cell(0, 8, line, ln=True)
    return bytes(pdf.output())


def _upload(client, headers, data: bytes, filename: str = "resume.pdf"):
    return client.post(
        "/brain/import-resume",
        headers=headers,
        files={"file": (filename, data, "application/pdf")},
    )


def test_import_resume_creates_and_fills_brain(client, auth_headers):
    headers = auth_headers()
    response = _upload(client, headers, _resume_pdf_bytes())
    assert response.status_code == 200
    brain = response.json()["brain"]
    assert brain["identity"]["full_name"] == "Ada Lovelace"
    assert brain["identity"]["email"] == "ada@example.com"
    assert brain["identity"]["summary"]
    skill_names = {s["name"] for s in brain["skills"]}
    assert {"Meta Ads", "Google Ads"} <= skill_names
    assert response.json()["imported"]["skills_added"] >= 3


def test_import_resume_merges_without_clobbering(client, auth_headers):
    headers = auth_headers()
    client.post("/brain", headers=headers, json={"full_name": "Real Name", "email": "real@me.com"})
    client.patch("/brain/summary", headers=headers, json={"summary": "My own words."})
    response = _upload(client, headers, _resume_pdf_bytes())
    assert response.status_code == 200
    brain = response.json()["brain"]
    # User-entered identity + summary are preserved; skills still merge in.
    assert brain["identity"]["full_name"] == "Real Name"
    assert brain["identity"]["summary"] == "My own words."
    assert any(s["name"] == "Meta Ads" for s in brain["skills"])


def test_import_resume_rejects_non_pdf(client, auth_headers):
    headers = auth_headers()
    response = client.post(
        "/brain/import-resume",
        headers=headers,
        files={"file": ("notes.txt", b"just text", "text/plain")},
    )
    assert response.status_code == 415


def test_import_resume_requires_auth(client):
    response = client.post(
        "/brain/import-resume", files={"file": ("r.pdf", b"%PDF-1.4", "application/pdf")}
    )
    assert response.status_code == 401
