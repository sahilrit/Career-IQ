"""Full-time vs. freelance vs. combined strategy comparison. Reuses
Phase 35's OpportunityValueBreakdown for the full-time side rather than
recomputing compensation value, and annualizes real freelance
IncomeRecords for the freelance side — an explicit projection, flagged
as such, not a guarantee.
"""

from __future__ import annotations

from pydantic import BaseModel

from careeros_financial_intelligence.income import IncomeRecord
from careeros_offer_negotiation import OpportunityValueBreakdown

DISCLAIMER = "Estimate only — freelance income is annualized from recent records, not guaranteed."


class FinancialComparison(BaseModel):
    full_time_value: float
    freelance_annualized_value: float
    combined_value: float
    disclaimer: str = DISCLAIMER


def annualized_freelance_income(records: list[IncomeRecord], *, months_covered: int) -> float:
    if months_covered <= 0:
        return 0.0
    total = sum(record.amount for record in records)
    return total / months_covered * 12


def compare_strategies(
    full_time_breakdown: OpportunityValueBreakdown,
    freelance_records: list[IncomeRecord],
    *,
    months_covered: int,
    freelance_capacity_fraction: float = 1.0,
) -> FinancialComparison:
    freelance_value = annualized_freelance_income(freelance_records, months_covered=months_covered)
    combined_value = (
        full_time_breakdown.opportunity_value + freelance_value * freelance_capacity_fraction
    )
    return FinancialComparison(
        full_time_value=full_time_breakdown.opportunity_value,
        freelance_annualized_value=freelance_value,
        combined_value=combined_value,
    )
