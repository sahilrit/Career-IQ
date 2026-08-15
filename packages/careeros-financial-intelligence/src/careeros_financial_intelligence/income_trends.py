"""Income trends: monthly totals computed directly from real
IncomeRecords, and a trend direction derived by comparing the first
half of the covered months against the second half — no forecasting,
just a summary of what already happened.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from careeros_financial_intelligence.income import IncomeRecord

_FLAT_THRESHOLD_PCT = 0.05


class TrendDirection(StrEnum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    FLAT = "flat"


class MonthlyTotal(BaseModel):
    year: int
    month: int
    total: float


def monthly_totals(records: list[IncomeRecord]) -> list[MonthlyTotal]:
    totals: dict[tuple[int, int], float] = {}
    for record in records:
        key = (record.received_date.year, record.received_date.month)
        totals[key] = totals.get(key, 0.0) + record.amount

    return [
        MonthlyTotal(year=year, month=month, total=total)
        for (year, month), total in sorted(totals.items())
    ]


def detect_trend(monthly: list[MonthlyTotal]) -> TrendDirection | None:
    if len(monthly) < 2:
        return None

    midpoint = len(monthly) // 2
    first_half = monthly[:midpoint]
    second_half = monthly[midpoint:]
    first_avg = sum(m.total for m in first_half) / len(first_half)
    second_avg = sum(m.total for m in second_half) / len(second_half)

    if first_avg == 0:
        return TrendDirection.FLAT if second_avg == 0 else TrendDirection.INCREASING

    change = (second_avg - first_avg) / first_avg
    if change > _FLAT_THRESHOLD_PCT:
        return TrendDirection.INCREASING
    if change < -_FLAT_THRESHOLD_PCT:
        return TrendDirection.DECREASING
    return TrendDirection.FLAT
