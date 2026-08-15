"""OfferNegotiationDivision: the facade tying offer storage, opportunity
value calculation, cross-offer comparison, and negotiation content
generation together.
"""

from __future__ import annotations

from careeros_offer_negotiation.comparison import RankedOffer, compare_offers
from careeros_offer_negotiation.negotiation import (
    generate_negotiation_talking_points,
    render_negotiation_script,
)
from careeros_offer_negotiation.offer import Offer, OfferRepository
from careeros_offer_negotiation.opportunity_value import (
    OpportunityValueBreakdown,
    calculate_opportunity_value,
)


class OfferNegotiationDivision:
    def __init__(self, offer_repository: OfferRepository) -> None:
        self._offers = offer_repository

    def add_offer(self, offer: Offer) -> None:
        self._offers.save(offer)

    def evaluate(
        self, offer_id: str, *, effective_tax_rate: float | None = None
    ) -> OpportunityValueBreakdown:
        offer = self._offers.load(offer_id)
        return calculate_opportunity_value(offer, effective_tax_rate=effective_tax_rate)

    def compare_all(self, *, effective_tax_rate: float | None = None) -> list[RankedOffer]:
        return compare_offers(self._offers.list_all(), effective_tax_rate=effective_tax_rate)

    def negotiation_talking_points(self, offer_id: str, target_base_salary: float) -> list[str]:
        offer = self._offers.load(offer_id)
        return generate_negotiation_talking_points(offer, target_base_salary)

    def negotiation_script(self, offer_id: str, target_base_salary: float) -> str:
        offer = self._offers.load(offer_id)
        return render_negotiation_script(offer, target_base_salary)
