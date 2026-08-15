"""Tests for the Opportunity unification of JobPosting/GigPosting."""

from __future__ import annotations

from careeros_freelance_providers import Budget, GigPosting
from careeros_job_providers import JobPosting, Salary
from careeros_opportunity_intelligence import OpportunityKind, from_gig_posting, from_job_posting


def test_from_job_posting_maps_company_to_organization_and_salary_to_compensation():
    posting = JobPosting(
        source_provider="remoteok",
        external_id="1",
        title="Backend Engineer",
        company_name="Acme",
        url="https://example.com/1",
        salary=Salary(min_amount=100_000, max_amount=140_000),
        tags=["python"],
    )
    opportunity = from_job_posting(posting)

    assert opportunity.kind == OpportunityKind.EMPLOYMENT
    assert opportunity.organization_name == "Acme"
    assert opportunity.compensation_amount == 120_000
    assert opportunity.tags == ["python"]


def test_from_gig_posting_maps_client_to_organization_and_budget_to_compensation():
    posting = GigPosting(
        source_provider="fiverr",
        external_id="1",
        title="Shopify redesign",
        client_name="ada_dev",
        url="https://example.com/1",
        budget=Budget(min_amount=400, max_amount=600),
        skills_required=["shopify"],
    )
    opportunity = from_gig_posting(posting)

    assert opportunity.kind == OpportunityKind.FREELANCE
    assert opportunity.organization_name == "ada_dev"
    assert opportunity.compensation_amount == 500
    assert opportunity.tags == ["shopify"]


def test_dedupe_key_distinguishes_kind_provider_and_id():
    job_posting = JobPosting(
        source_provider="remoteok",
        external_id="1",
        title="Engineer",
        company_name="Acme",
        url="https://example.com/1",
    )
    gig_posting = GigPosting(
        source_provider="remoteok",
        external_id="1",
        title="Engineer",
        client_name="Acme",
        url="https://example.com/1",
    )
    job_opportunity = from_job_posting(job_posting)
    gig_opportunity = from_gig_posting(gig_posting)

    assert job_opportunity.dedupe_key != gig_opportunity.dedupe_key


def test_missing_compensation_is_none():
    posting = JobPosting(
        source_provider="remoteok",
        external_id="1",
        title="Engineer",
        company_name="Acme",
        url="https://example.com/1",
    )
    assert from_job_posting(posting).compensation_amount is None
