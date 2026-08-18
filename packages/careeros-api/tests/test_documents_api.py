"""Generated documents: persistence via /opportunities/generate, versioning,
editing, and PDF export."""

from __future__ import annotations

from careeros_api import dependencies
from careeros_career_brain import Application, CareerBrain, CareerBrainRepository, Identity
from careeros_career_brain.models import Skill
from careeros_job_discovery import JobPostingRepository
from careeros_job_providers import JobPosting
from careeros_tenancy import TenantScopedDocumentStore


def _seed(client, headers):
    workspace_id = client.get("/auth/me", headers=headers).json()["workspace_id"]
    scoped = TenantScopedDocumentStore(dependencies.get_store(), workspace_id)
    brain = CareerBrain(
        identity=Identity(full_name="Sahil Sachdeva", email="sahilrit09@gmail.com"),
        skills=[Skill(name="Meta Ads"), Skill(name="CRO")],
    )
    posting = JobPosting(
        source_provider="test",
        external_id="1",
        title="Growth Marketer",
        company_name="Ramp",
        url="https://jobs/1",
        description="Own Meta Ads and CRO for a DTC brand.",
        tags=["Meta Ads", "CRO"],
    )
    JobPostingRepository(scoped).save(posting)
    application = Application(
        job_title="Growth Marketer", company_name="Ramp", job_url="https://jobs/1"
    )
    brain.applications.append(application)
    CareerBrainRepository(scoped).save(brain)
    return application.id


def test_generate_persists_versioned_documents(client, auth_headers):
    headers = auth_headers()
    app_id = _seed(client, headers)

    r1 = client.post("/opportunities/generate", headers=headers, json={"job_url": "https://jobs/1"})
    assert r1.status_code == 200
    body = r1.json()
    assert body["resume_document_id"] and body["cover_letter_document_id"]
    assert body["version"] == 1

    # regenerating creates a new version, not a clobber
    r2 = client.post("/opportunities/generate", headers=headers, json={"job_url": "https://jobs/1"})
    assert r2.json()["version"] == 2

    docs = client.get(f"/applications/{app_id}/documents", headers=headers).json()
    assert len(docs) == 4  # resume + cover_letter, each at v1 and v2
    assert {d["kind"] for d in docs} == {"resume", "cover_letter"}


def test_edit_document(client, auth_headers):
    headers = auth_headers()
    _seed(client, headers)
    doc_id = client.post(
        "/opportunities/generate", headers=headers, json={"job_url": "https://jobs/1"}
    ).json()["resume_document_id"]
    r = client.patch(f"/documents/{doc_id}", headers=headers, json={"content": "My edited résumé."})
    assert r.status_code == 200 and r.json()["content"] == "My edited résumé."


def test_export_pdf(client, auth_headers):
    headers = auth_headers()
    _seed(client, headers)
    doc_id = client.post(
        "/opportunities/generate", headers=headers, json={"job_url": "https://jobs/1"}
    ).json()["resume_document_id"]
    r = client.get(f"/documents/{doc_id}/pdf", headers=headers)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"  # a real PDF was produced


def test_document_not_found_is_404(client, auth_headers):
    headers = auth_headers()
    assert client.get("/documents/nope/pdf", headers=headers).status_code == 404
    assert (
        client.patch("/documents/nope", headers=headers, json={"content": "x"}).status_code == 404
    )


def test_documents_require_auth(client):
    assert client.get("/applications/x/documents").status_code == 401
