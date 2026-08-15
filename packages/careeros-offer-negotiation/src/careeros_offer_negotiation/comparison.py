"""Compares multiple offers by Opportunity Value rather than salary
alone — the roadmap's "full-time vs. freelance vs. combined strategy"
comparison, one offer at a time.
"""

from __future__ import annotations

from pydantic import BaseModel

from careeros_offer_negotiation.offer import Offer
from careeros_offer_negotiation.opportunity_value import (
    OpportunityValueBreakdown,
    calculate_opportunity_value,
)


class RankedOffer(BaseModel):
    offer: Offer
    breakdown: OpportunityValueBreakdown


def compare_offers(
    offers: list[Offer], *, effective_tax_rate: float | None = None
) -> list[RankedOffer]:
    ranked = [
        RankedOffer(
            offer=offer,
            breakdown=calculate_opportunity_value(offer, effective_tax_rate=effective_tax_rate),
        )
        for offer in offers
    ]
    ranked.sort(key=lambda r: r.breakdown.opportunity_value, reverse=True)
    return ranked
