"""Tests for annualized_freelance_income / compare_strategies."""

from __future__ import annotations

from careeros_financial_intelligence import annualized_freelance_income, compare_strategies
from careeros_financial_intelligence.strategy_comparison import DISCLAIMER


def test_annualized_income_extrapolates_to_twelve_months(salary_record_factory):
    records = [salary_record_factory(amount=1_000)]
    assert annualized_freelance_income(records, months_covered=1) == 12_000


def test_annualized_income_with_zero_months_is_zero(salary_record_factory):
    records = [salary_record_factory(amount=1_000)]
    assert annualized_freelance_income(records, months_covered=0) == 0.0


def test_compare_strategies_combines_full_time_and_freelance(
    full_time_breakdown, salary_record_factory
):
    freelance_records = [salary_record_factory(amount=1_000)]
    comparison = compare_strategies(full_time_breakdown, freelance_records, months_covered=1)
    assert comparison.full_time_value == full_time_breakdown.opportunity_value
    assert comparison.freelance_annualized_value == 12_000
    assert comparison.combined_value == full_time_breakdown.opportunity_value + 12_000


def test_compare_strategies_applies_capacity_fraction(full_time_breakdown, salary_record_factory):
    freelance_records = [salary_record_factory(amount=1_000)]
    comparison = compare_strategies(
        full_time_breakdown, freelance_records, months_covered=1, freelance_capacity_fraction=0.5
    )
    assert comparison.combined_value == full_time_breakdown.opportunity_value + 6_000


def test_disclaimer_is_present(full_time_breakdown):
    comparison = compare_strategies(full_time_breakdown, [], months_covered=1)
    assert comparison.disclaimer == DISCLAIMER
