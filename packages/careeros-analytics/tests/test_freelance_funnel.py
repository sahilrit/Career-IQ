"""Tests for compute_freelance_funnel."""

from __future__ import annotations

from datetime import date

from careeros_analytics import compute_freelance_funnel
from careeros_client_acquisition import (
    ClientAcquisitionProgressRepository,
    ClientAcquisitionStage,
    Company,
)
from careeros_financial_intelligence import IncomeRecord, IncomeSource


def test_lead_count_is_every_company(store):
    companies = [Company(name="A", website="https://a.example.com")]
    metrics = compute_freelance_funnel(companies, ClientAcquisitionProgressRepository(store), [])
    assert metrics.lead_count == 1
    assert metrics.outreach_count == 0


def test_stage_counts_reflect_real_progress(store):
    company = Company(name="A", website="https://a.example.com")
    progress_repository = ClientAcquisitionProgressRepository(store)
    progress_repository.mark_complete(company.id, ClientAcquisitionStage.OUTREACH)
    progress_repository.mark_complete(company.id, ClientAcquisitionStage.PROPOSAL)

    metrics = compute_freelance_funnel([company], progress_repository, [])
    assert metrics.outreach_count == 1
    assert metrics.proposal_count == 1
    assert metrics.call_count == 0
    assert metrics.client_count == 0


def test_total_revenue_includes_freelance_and_client_revenue_only(store):
    income_records = [
        IncomeRecord(
            source=IncomeSource.FREELANCE,
            source_name="Client A",
            amount=500,
            received_date=date(2026, 1, 1),
        ),
        IncomeRecord(
            source=IncomeSource.CLIENT_REVENUE,
            source_name="Client B",
            amount=300,
            received_date=date(2026, 1, 1),
        ),
        IncomeRecord(
            source=IncomeSource.SALARY,
            source_name="Employer",
            amount=10_000,
            received_date=date(2026, 1, 1),
        ),
    ]
    metrics = compute_freelance_funnel(
        [], ClientAcquisitionProgressRepository(store), income_records
    )
    assert metrics.total_revenue == 800
