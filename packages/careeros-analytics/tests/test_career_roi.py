"""Tests for compute_career_roi."""

from __future__ import annotations

from datetime import date

from careeros_analytics import DISCLAIMER, compute_career_roi
from careeros_financial_intelligence import IncomeRecord, IncomeSource
from careeros_offer_negotiation import Offer


def _income(source: IncomeSource, amount: float) -> IncomeRecord:
    return IncomeRecord(
        source=source, source_name="test", amount=amount, received_date=date(2026, 1, 1)
    )


def test_financial_total_sums_salary_freelance_and_equity():
    income_records = [
        _income(IncomeSource.SALARY, 10_000),
        _income(IncomeSource.FREELANCE, 2_000),
    ]
    offers = [
        Offer(company_name="Acme", job_title="Engineer", base_salary=100_000, equity_value=5_000)
    ]
    roi = compute_career_roi(
        income_records=income_records,
        open_offers=offers,
        network_contact_count=10,
        skill_count=5,
    )
    assert roi.salary_income == 10_000
    assert roi.freelance_income == 2_000
    assert roi.equity_value == 5_000
    assert roi.financial_total == 17_000


def test_non_financial_fields_are_reported_not_folded_in():
    roi = compute_career_roi(
        income_records=[], open_offers=[], network_contact_count=10, skill_count=5
    )
    assert roi.network_contact_count == 10
    assert roi.skill_count == 5
    assert roi.financial_total == 0


def test_future_opportunity_value_reflects_open_offers():
    offers = [Offer(company_name="Acme", job_title="Engineer", base_salary=100_000)]
    roi = compute_career_roi(
        income_records=[], open_offers=offers, network_contact_count=0, skill_count=0
    )
    assert roi.future_opportunity_value == 100_000


def test_disclaimer_is_present():
    roi = compute_career_roi(
        income_records=[], open_offers=[], network_contact_count=0, skill_count=0
    )
    assert roi.disclaimer == DISCLAIMER
