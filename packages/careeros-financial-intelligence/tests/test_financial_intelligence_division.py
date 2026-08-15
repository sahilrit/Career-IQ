"""Tests for the FinancialIntelligenceDivision facade."""

from __future__ import annotations

from datetime import date

import pytest

from careeros_financial_intelligence import FinancialIntelligenceDivision, IncomeSource


@pytest.fixture
def division(income_repository):
    return FinancialIntelligenceDivision(income_repository)


def test_total_income_sums_all_records(division, salary_record_factory):
    division.add_income(salary_record_factory(amount=1_000))
    division.add_income(salary_record_factory(amount=2_000))
    assert division.total_income() == 3_000


def test_total_income_filters_by_source(division, salary_record_factory):
    division.add_income(salary_record_factory(amount=1_000, source=IncomeSource.SALARY))
    division.add_income(salary_record_factory(amount=500, source=IncomeSource.FREELANCE))
    assert division.total_income(IncomeSource.FREELANCE) == 500


def test_effective_hourly_rate_delegates(division, salary_record_factory):
    record = salary_record_factory(amount=1_000, hours_worked=10)
    division.add_income(record)
    assert division.effective_hourly_rate(record.id) == 100.0


def test_monthly_totals_delegates(division, salary_record_factory):
    division.add_income(salary_record_factory(amount=1_000, received_date=date(2026, 1, 1)))
    totals = division.monthly_totals()
    assert len(totals) == 1


def test_income_trend_delegates(division, salary_record_factory):
    division.add_income(salary_record_factory(amount=1_000, received_date=date(2026, 1, 1)))
    division.add_income(salary_record_factory(amount=2_000, received_date=date(2026, 2, 1)))
    assert division.income_trend() is not None


def test_compare_strategies_uses_freelance_records(
    division, salary_record_factory, full_time_breakdown
):
    division.add_income(
        salary_record_factory(
            amount=1_000, source=IncomeSource.FREELANCE, received_date=date(2026, 1, 1)
        )
    )
    comparison = division.compare_strategies(full_time_breakdown, months_covered=1)
    assert comparison.freelance_annualized_value == 12_000
