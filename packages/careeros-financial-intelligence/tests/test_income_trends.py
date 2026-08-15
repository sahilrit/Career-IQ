"""Tests for monthly_totals / detect_trend."""

from __future__ import annotations

from datetime import date

from careeros_financial_intelligence import (
    MonthlyTotal,
    TrendDirection,
    detect_trend,
    monthly_totals,
)


def test_monthly_totals_groups_and_sums_by_month(salary_record_factory):
    records = [
        salary_record_factory(amount=1_000, received_date=date(2026, 1, 5)),
        salary_record_factory(amount=500, received_date=date(2026, 1, 20)),
        salary_record_factory(amount=2_000, received_date=date(2026, 2, 1)),
    ]
    totals = monthly_totals(records)
    assert totals == [
        MonthlyTotal(year=2026, month=1, total=1_500.0),
        MonthlyTotal(year=2026, month=2, total=2_000.0),
    ]


def test_monthly_totals_is_chronologically_sorted(salary_record_factory):
    records = [
        salary_record_factory(amount=1_000, received_date=date(2026, 3, 1)),
        salary_record_factory(amount=1_000, received_date=date(2026, 1, 1)),
    ]
    totals = monthly_totals(records)
    assert [(t.year, t.month) for t in totals] == [(2026, 1), (2026, 3)]


def test_detect_trend_with_fewer_than_two_months_is_none(salary_record_factory):
    totals = monthly_totals([salary_record_factory()])
    assert detect_trend(totals) is None


def test_detect_trend_increasing(salary_record_factory):
    records = [
        salary_record_factory(amount=1_000, received_date=date(2026, 1, 1)),
        salary_record_factory(amount=2_000, received_date=date(2026, 2, 1)),
    ]
    assert detect_trend(monthly_totals(records)) == TrendDirection.INCREASING


def test_detect_trend_decreasing(salary_record_factory):
    records = [
        salary_record_factory(amount=2_000, received_date=date(2026, 1, 1)),
        salary_record_factory(amount=1_000, received_date=date(2026, 2, 1)),
    ]
    assert detect_trend(monthly_totals(records)) == TrendDirection.DECREASING


def test_detect_trend_flat(salary_record_factory):
    records = [
        salary_record_factory(amount=1_000, received_date=date(2026, 1, 1)),
        salary_record_factory(amount=1_010, received_date=date(2026, 2, 1)),
    ]
    assert detect_trend(monthly_totals(records)) == TrendDirection.FLAT
