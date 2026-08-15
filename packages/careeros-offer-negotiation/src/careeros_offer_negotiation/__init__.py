"""careeros_offer_negotiation: Offer Evaluation & Negotiation Intelligence.

Analyzes an offer beyond salary alone (bonus, equity, benefits, PTO,
remote policy, stability, growth, reputation, tax implications) and
calculates a single, transparent Opportunity Value for comparing offers.
"""

from careeros_offer_negotiation.comparison import RankedOffer, compare_offers
from careeros_offer_negotiation.exceptions import OfferNegotiationError
from careeros_offer_negotiation.negotiation import (
    generate_negotiation_talking_points,
    render_negotiation_script,
)
from careeros_offer_negotiation.offer import Offer, OfferRepository
from careeros_offer_negotiation.offer_negotiation_division import OfferNegotiationDivision
from careeros_offer_negotiation.opportunity_value import (
    DISCLAIMER,
    OpportunityValueBreakdown,
    calculate_opportunity_value,
)

__all__ = [
    "DISCLAIMER",
    "Offer",
    "OfferNegotiationDivision",
    "OfferNegotiationError",
    "OfferRepository",
    "OpportunityValueBreakdown",
    "RankedOffer",
    "calculate_opportunity_value",
    "compare_offers",
    "generate_negotiation_talking_points",
    "render_negotiation_script",
]
