"""Effective hourly rate: the real amount earned divided by the real
hours worked to earn it — only computable when both are known.
"""

from __future__ import annotations

from careeros_financial_intelligence.income import IncomeRecord


def calculate_effective_hourly_rate(record: IncomeRecord) -> float | None:
    if not record.hours_worked:
        return None
    return record.amount / record.hours_worked
