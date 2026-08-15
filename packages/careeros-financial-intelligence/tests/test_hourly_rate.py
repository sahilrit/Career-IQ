"""Tests for calculate_effective_hourly_rate."""

from __future__ import annotations

from careeros_financial_intelligence import calculate_effective_hourly_rate


def test_computes_amount_divided_by_hours(salary_record_factory):
    record = salary_record_factory(amount=1_000, hours_worked=10)
    assert calculate_effective_hourly_rate(record) == 100.0


def test_returns_none_when_hours_worked_is_none(salary_record_factory):
    record = salary_record_factory(hours_worked=None)
    assert calculate_effective_hourly_rate(record) is None


def test_returns_none_when_hours_worked_is_zero(salary_record_factory):
    record = salary_record_factory(hours_worked=0)
    assert calculate_effective_hourly_rate(record) is None
