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


# --- Regression: bugs found in the 2026-08-18 deep audit ----------------------


def _make_brain(client, headers):
    client.post("/brain", headers=headers, json={"full_name": "Ada", "email": "ada@example.com"})


def test_experience_end_before_start_is_422_not_500(client, auth_headers):
    """Swapped dates are a common typo — must be a friendly 422, never a 500."""
    headers = auth_headers()
    _make_brain(client, headers)
    response = client.post(
        "/brain/experience",
        headers=headers,
        json={
            "company_name": "Acme",
            "title": "Growth Lead",
            "start_date": "2022-01-01",
            "end_date": "2020-01-01",
        },
    )
    assert response.status_code == 422
    assert "end_date" in response.json()["detail"]


def test_update_preferences_sets_min_salary(client, auth_headers):
    headers = auth_headers()
    _make_brain(client, headers)
    response = client.patch("/brain/preferences", headers=headers, json={"min_salary": 140000})
    assert response.status_code == 200
    assert response.json()["preferences"]["min_salary"] == 140000


def test_update_preferences_negative_salary_is_422(client, auth_headers):
    headers = auth_headers()
    _make_brain(client, headers)
    response = client.patch("/brain/preferences", headers=headers, json={"min_salary": -5})
    assert response.status_code == 422


def test_update_preferences_partial_does_not_clobber(client, auth_headers):
    headers = auth_headers()
    _make_brain(client, headers)
    client.patch("/brain/preferences", headers=headers, json={"min_salary": 120000})
    client.patch("/brain/preferences", headers=headers, json={"remote_only": True})
    prefs = client.get("/brain", headers=headers).json()["preferences"]
    assert prefs["min_salary"] == 120000  # not wiped by the second partial update
    assert prefs["remote_only"] is True


# --- Remove skills / experience + résumé experience import -------------------


def test_remove_skill(client, auth_headers):
    headers = auth_headers()
    _make_brain(client, headers)
    brain = client.post("/brain/skills", headers=headers, json={"name": "Meta Ads"}).json()
    skill_id = brain["skills"][0]["id"]
    r = client.delete(f"/brain/skills/{skill_id}", headers=headers)
    assert r.status_code == 200 and r.json()["skills"] == []
    assert client.delete(f"/brain/skills/{skill_id}", headers=headers).status_code == 404


def test_remove_experience(client, auth_headers):
    headers = auth_headers()
    _make_brain(client, headers)
    brain = client.post(
        "/brain/experience",
        headers=headers,
        json={"company_name": "Acme", "title": "Lead", "start_date": "2021-01-01"},
    ).json()
    exp_id = brain["experiences"][0]["id"]
    r = client.delete(f"/brain/experience/{exp_id}", headers=headers)
    assert r.status_code == 200 and r.json()["experiences"] == []


def test_import_resume_merges_experiences(client, auth_headers, monkeypatch):
    from datetime import date

    from careeros_api.routers import brain as brain_router
    from careeros_career_brain import ParsedExperience, ParsedResume

    headers = auth_headers()
    _make_brain(client, headers)
    fake = ParsedResume(
        full_name="Sahil",
        skills=["Meta Ads"],
        experiences=[
            ParsedExperience(title="Senior Marketer", company="Acme", start_date=date(2021, 1, 1))
        ],
    )
    monkeypatch.setattr(brain_router, "extract_text_from_pdf", lambda data: "resume text")
    monkeypatch.setattr(brain_router, "parse_resume", lambda text: fake)
    r = client.post(
        "/brain/import-resume",
        headers=headers,
        files={"file": ("cv.pdf", b"%PDF-fake-bytes", "application/pdf")},
    )
    assert r.status_code == 200
    assert r.json()["imported"]["experiences_added"] == 1
    assert r.json()["brain"]["experiences"][0]["company_name"] == "Acme"


# --- First-run questionnaire (focus preference) ------------------------------


def test_set_focus_and_titles(client, auth_headers):
    headers = auth_headers()
    _make_brain(client, headers)
    r = client.patch(
        "/brain/preferences",
        headers=headers,
        json={"focus": "freelance", "desired_titles": ["Growth Lead"], "remote_only": True},
    )
    assert r.status_code == 200
    prefs = r.json()["preferences"]
    assert prefs["focus"] == "freelance"
    assert prefs["desired_titles"] == ["Growth Lead"]


def test_invalid_focus_is_422(client, auth_headers):
    headers = auth_headers()
    _make_brain(client, headers)
    r = client.patch("/brain/preferences", headers=headers, json={"focus": "vacation"})
    assert r.status_code == 422


# --- Education & certifications (more CV sections) ----------------------------


def test_add_and_remove_education(client, auth_headers):
    headers = auth_headers()
    _make_brain(client, headers)
    brain = client.post(
        "/brain/education",
        headers=headers,
        json={"institution": "IIT", "credential": "B.Tech", "end_date": "2019-06-01"},
    ).json()
    assert brain["education"][0]["institution"] == "IIT"
    edu_id = brain["education"][0]["id"]
    r = client.delete(f"/brain/education/{edu_id}", headers=headers)
    assert r.status_code == 200 and r.json()["education"] == []
    assert client.delete(f"/brain/education/{edu_id}", headers=headers).status_code == 404


def test_add_and_remove_certification(client, auth_headers):
    headers = auth_headers()
    _make_brain(client, headers)
    brain = client.post(
        "/brain/certifications",
        headers=headers,
        json={"name": "Google Ads", "issuer": "Google"},
    ).json()
    assert brain["certifications"][0]["name"] == "Google Ads"
    cert_id = brain["certifications"][0]["id"]
    assert client.delete(f"/brain/certifications/{cert_id}", headers=headers).status_code == 200


def test_education_requires_fields(client, auth_headers):
    headers = auth_headers()
    _make_brain(client, headers)
    assert (
        client.post("/brain/education", headers=headers, json={"institution": "X"}).status_code
        == 422
    )


# --- Projects, languages, awards ---------------------------------------------


def test_add_and_remove_project(client, auth_headers):
    headers = auth_headers()
    _make_brain(client, headers)
    brain = client.post(
        "/brain/projects",
        headers=headers,
        json={"name": "Portfolio", "url": "https://sahilsachdevaprojects.netlify.app/"},
    ).json()
    assert brain["projects"][0]["name"] == "Portfolio"
    pid = brain["projects"][0]["id"]
    assert client.delete(f"/brain/projects/{pid}", headers=headers).status_code == 200
    assert client.delete(f"/brain/projects/{pid}", headers=headers).status_code == 404


def test_add_and_remove_language(client, auth_headers):
    headers = auth_headers()
    _make_brain(client, headers)
    brain = client.post(
        "/brain/languages", headers=headers, json={"name": "English", "proficiency": "fluent"}
    ).json()
    assert brain["languages"][0] == {
        **brain["languages"][0],
        "name": "English",
        "proficiency": "fluent",
    }
    lid = brain["languages"][0]["id"]
    assert client.delete(f"/brain/languages/{lid}", headers=headers).status_code == 200


def test_add_and_remove_award(client, auth_headers):
    headers = auth_headers()
    _make_brain(client, headers)
    brain = client.post(
        "/brain/awards", headers=headers, json={"title": "Top Performer", "issuer": "Acme"}
    ).json()
    assert brain["awards"][0]["title"] == "Top Performer"
    aid = brain["awards"][0]["id"]
    assert client.delete(f"/brain/awards/{aid}", headers=headers).status_code == 200


def test_new_sections_require_fields(client, auth_headers):
    headers = auth_headers()
    _make_brain(client, headers)
    assert client.post("/brain/projects", headers=headers, json={}).status_code == 422
    assert client.post("/brain/languages", headers=headers, json={}).status_code == 422
    assert client.post("/brain/awards", headers=headers, json={}).status_code == 422


def test_reimport_replaces_resume_roles_keeps_manual(client, auth_headers, monkeypatch):
    from datetime import date

    from careeros_api.routers import brain as brain_router
    from careeros_career_brain import ParsedExperience, ParsedResume

    headers = auth_headers()
    _make_brain(client, headers)
    # a hand-typed role that must survive re-imports
    client.post(
        "/brain/experience",
        headers=headers,
        json={"company_name": "Manual Co", "title": "Manual Role", "start_date": "2020-01-01"},
    )
    fake = ParsedResume(
        experiences=[
            ParsedExperience(title="Senior Marketer", company="Acme", start_date=date(2021, 1, 1))
        ]
    )
    monkeypatch.setattr(brain_router, "extract_text_from_pdf", lambda data: "resume text")
    monkeypatch.setattr(brain_router, "parse_resume", lambda text: fake)

    def upload():
        return client.post(
            "/brain/import-resume",
            headers=headers,
            files={"file": ("cv.pdf", b"%PDF-x", "application/pdf")},
        )

    upload()
    body = upload().json()  # re-import
    titles = sorted(e["title"] for e in body["brain"]["experiences"])
    # manual kept, résumé role present exactly once (not duplicated)
    assert titles == ["Manual Role", "Senior Marketer"]


def test_import_resume_merges_education_and_certifications(client, auth_headers, monkeypatch):
    from datetime import date

    from careeros_api.routers import brain as brain_router
    from careeros_career_brain import (
        ParsedCertification,
        ParsedEducation,
        ParsedResume,
    )

    headers = auth_headers()
    _make_brain(client, headers)
    fake = ParsedResume(
        education=[
            ParsedEducation(institution="Axis College", credential="BCA", end_date=date(2023, 1, 1))
        ],
        certifications=[ParsedCertification(name="Digital Marketing", issuer="HubSpot")],
    )
    monkeypatch.setattr(brain_router, "extract_text_from_pdf", lambda data: "resume text")
    monkeypatch.setattr(brain_router, "parse_resume", lambda text: fake)
    body = client.post(
        "/brain/import-resume",
        headers=headers,
        files={"file": ("cv.pdf", b"%PDF-x", "application/pdf")},
    ).json()
    assert body["imported"]["education_added"] == 1
    assert body["imported"]["certifications_added"] == 1
    assert body["brain"]["education"][0]["institution"] == "Axis College"
    assert body["brain"]["certifications"][0]["name"] == "Digital Marketing"
