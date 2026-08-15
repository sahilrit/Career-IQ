"""FinancialIntelligenceDivision: the facade tying income tracking,
effective hourly rate, income trends, and strategy comparison together.
"""

from __future__ import annotations

from careeros_financial_intelligence.hourly_rate import calculate_effective_hourly_rate
from careeros_financial_intelligence.income import IncomeRecord, IncomeRepository, IncomeSource
from careeros_financial_intelligence.income_trends import (
    MonthlyTotal,
    TrendDirection,
    detect_trend,
    monthly_totals,
)
from careeros_financial_intelligence.strategy_comparison import (
    FinancialComparison,
    compare_strategies,
)
from careeros_offer_negotiation import OpportunityValueBreakdown


class FinancialIntelligenceDivision:
    def __init__(self, income_repository: IncomeRepository) -> None:
        self._income = income_repository

    def add_income(self, record: IncomeRecord) -> None:
        self._income.save(record)

    def total_income(self, source: IncomeSource | None = None) -> float:
        records = self._income.list_all() if source is None else self._income.list_by_source(source)
        return sum(record.amount for record in records)

    def effective_hourly_rate(self, record_id: str) -> float | None:
        return calculate_effective_hourly_rate(self._income.load(record_id))

    def monthly_totals(self, source: IncomeSource | None = None) -> list[MonthlyTotal]:
        records = self._income.list_all() if source is None else self._income.list_by_source(source)
        return monthly_totals(records)

    def income_trend(self, source: IncomeSource | None = None) -> TrendDirection | None:
        return detect_trend(self.monthly_totals(source))

    def compare_strategies(
        self,
        full_time_breakdown: OpportunityValueBreakdown,
        *,
        months_covered: int,
        freelance_capacity_fraction: float = 1.0,
    ) -> FinancialComparison:
        freelance_records = self._income.list_by_source(IncomeSource.FREELANCE)
        return compare_strategies(
            full_time_breakdown,
            freelance_records,
            months_covered=months_covered,
            freelance_capacity_fraction=freelance_capacity_fraction,
        )
