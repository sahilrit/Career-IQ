"""Opportunity Value: a transparent, documented formula for comparing
offers on more than salary alone — not a guarantee, just a consistent
way to weigh compensation against the qualitative factors (stability,
growth, reputation) the roadmap calls for.

    pretax_total       = base + bonus + equity + benefits
    after_tax_total     = pretax_total * (1 - effective_tax_rate)
    qualitative_multiplier = 1.0 + (avg(stability, growth, reputation) - 3) * 0.05
    opportunity_value   = after_tax_total * qualitative_multiplier

Each unrated qualitative score defaults to 3 (neutral), so an offer
with no ratings at all gets a multiplier of exactly 1.0.
"""

from __future__ import annotations

from pydantic import BaseModel

from careeros_offer_negotiation.offer import Offer

DISCLAIMER = "Estimate only, based on a transparent heuristic — not financial advice."
_NEUTRAL_SCORE = 3
_MULTIPLIER_STEP = 0.05


class OpportunityValueBreakdown(BaseModel):
    offer_id: str
    pretax_total: float
    after_tax_total: float
    qualitative_multiplier: float
    opportunity_value: float
    disclaimer: str = DISCLAIMER


def calculate_opportunity_value(
    offer: Offer, *, effective_tax_rate: float | None = None
) -> OpportunityValueBreakdown:
    pretax_total = offer.base_salary + offer.bonus + offer.equity_value + offer.benefits_value

    after_tax_total = pretax_total
    if effective_tax_rate is not None:
        after_tax_total = pretax_total * (1 - effective_tax_rate)

    scores = [
        score
        for score in (offer.stability_score, offer.growth_score, offer.reputation_score)
        if score is not None
    ]
    avg_score = sum(scores) / len(scores) if scores else _NEUTRAL_SCORE
    qualitative_multiplier = 1.0 + (avg_score - _NEUTRAL_SCORE) * _MULTIPLIER_STEP

    return OpportunityValueBreakdown(
        offer_id=offer.id,
        pretax_total=pretax_total,
        after_tax_total=after_tax_total,
        qualitative_multiplier=qualitative_multiplier,
        opportunity_value=after_tax_total * qualitative_multiplier,
    )
