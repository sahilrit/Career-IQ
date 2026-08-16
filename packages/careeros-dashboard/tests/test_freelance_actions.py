"""Tests for the freelance client-acquisition glue, using a fake browser
session so the website audit runs without a real browser."""

from __future__ import annotations

from datetime import date

import pytest

from careeros_browser import FakeBrowserSession
from careeros_career_brain import CareerBrain, Identity, Skill
from careeros_client_acquisition import ClientAcquisitionProgressRepository, ClientAcquisitionStage
from careeros_common import DocumentStore
from careeros_dashboard.freelance_actions import (
    add_company,
    audit_company,
    list_companies,
    mark_outreach_sent,
    promote_to_client,
    record_client_income,
)
from careeros_financial_intelligence import IncomeRepository, IncomeSource
from careeros_opportunity_intelligence import ClientRepository, RelationshipStage


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def brain():
    return CareerBrain(
        identity=Identity(full_name="Sahil Sachdeva", email="sahil@example.com"),
        skills=[Skill(name="Shopify"), Skill(name="Meta Ads")],
    )


def test_add_company_normalizes_url_and_marks_discovery(store):
    company = add_company(store, name="Acme DTC", website="acme.com", industry="ecommerce")
    assert company.website == "https://acme.com"
    assert [c.name for c in list_companies(store)] == ["Acme DTC"]
    progress = ClientAcquisitionProgressRepository(store).load(company.id)
    assert ClientAcquisitionStage.DISCOVERY in progress.completed_stages


def test_audit_detects_signals_scores_and_drafts_outreach(store, brain):
    company = add_company(store, name="Acme DTC", website="http://acme.com")
    # A bare fake page: no https, no meta description, no testimonials/chat,
    # thin content -> several problem signals.
    session = FakeBrowserSession()
    session.goto("http://acme.com")

    outcome = audit_company(store, brain, company, session=session)

    assert outcome.signals  # problems were found
    assert outcome.opportunity_score > 0
    assert outcome.qualified is True
    assert "Acme DTC" in outcome.outreach_message
    assert outcome.report_text

    progress = ClientAcquisitionProgressRepository(store).load(company.id)
    assert ClientAcquisitionStage.AUDIT in progress.completed_stages


def test_mark_outreach_sent_advances_stage(store, brain):
    company = add_company(store, name="Acme", website="acme.com")
    mark_outreach_sent(store, company)
    progress = ClientAcquisitionProgressRepository(store).load(company.id)
    assert ClientAcquisitionStage.OUTREACH in progress.completed_stages


def test_promote_to_client_creates_client(store):
    company = add_company(store, name="Acme", website="acme.com")
    client = promote_to_client(store, company)
    assert client.stage == RelationshipStage.CONTACTED
    assert ClientRepository(store).find_by_name("Acme") is not None


def test_record_client_income_is_tagged_freelance(store):
    record_client_income(
        store, client_name="Acme", amount=2500.0, received_date=date(2026, 8, 1), hours_worked=10
    )
    records = IncomeRepository(store).list_by_source(IncomeSource.FREELANCE)
    assert len(records) == 1
    assert records[0].amount == 2500.0
    assert records[0].source_name == "Acme"


def test_generate_deep_deliverables_builds_full_pitch_kit(store, brain, tmp_path):
    from careeros_dashboard.freelance_actions import generate_deep_deliverables

    company = add_company(store, name="Acme DTC", website="https://acme.com")
    session = FakeBrowserSession()  # bare storefront -> findings across categories

    kit = generate_deep_deliverables(
        store,
        brain,
        company,
        monthly_visitors=10000,
        conversion_rate=0.02,
        average_order_value=50.0,
        output_dir=tmp_path,
        session=session,
    )

    assert kit.findings  # deep audit surfaced problems
    assert kit.roi_estimate is not None
    assert kit.roi_estimate.projected_additional_monthly_revenue > 0
    assert "Acme DTC" in kit.email
    assert kit.linkedin_message and kit.loom_script and kit.proposal
    assert kit.pdf_path.exists()
