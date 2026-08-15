"""Career ROI: the roadmap's "salary + freelance revenue + equity +
network + personal brand + skills + future opportunity value" —
deliberately reported as a breakdown, not one blended number.

Salary, freelance income, and equity are real dollars and get summed
into ``financial_total``. Network, skills, and future opportunity value
don't share a unit with dollars — pretending they do would mean
fabricating a conversion rate that doesn't exist, so they're reported
alongside the financial total instead of folded into it.
"""

from __future__ import annotations

from pydantic import BaseModel

from careeros_financial_intelligence import IncomeRecord, IncomeSource
from careeros_offer_negotiation import Offer, calculate_opportunity_value

DISCLAIMER = (
    "Financial components (salary, freelance income, equity) are summed as real dollars. "
    "Network, skill, and future-opportunity figures are reported alongside, not folded in — "
    "they don't share a unit with dollars."
)


class CareerROIBreakdown(BaseModel):
    salary_income: float
    freelance_income: float
    equity_value: float
    financial_total: float
    network_contact_count: int
    skill_count: int
    future_opportunity_value: float
    disclaimer: str = DISCLAIMER


def compute_career_roi(
    *,
    income_records: list[IncomeRecord],
    open_offers: list[Offer],
    network_contact_count: int,
    skill_count: int,
) -> CareerROIBreakdown:
    salary_income = sum(r.amount for r in income_records if r.source == IncomeSource.SALARY)
    freelance_income = sum(
        r.amount
        for r in income_records
        if r.source in (IncomeSource.FREELANCE, IncomeSource.CLIENT_REVENUE)
    )
    equity_value = sum(offer.equity_value for offer in open_offers)
    future_opportunity_value = sum(
        calculate_opportunity_value(offer).opportunity_value for offer in open_offers
    )

    return CareerROIBreakdown(
        salary_income=salary_income,
        freelance_income=freelance_income,
        equity_value=equity_value,
        financial_total=salary_income + freelance_income + equity_value,
        network_contact_count=network_contact_count,
        skill_count=skill_count,
        future_opportunity_value=future_opportunity_value,
    )
