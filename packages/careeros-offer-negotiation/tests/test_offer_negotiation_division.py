"""Tests for the OfferNegotiationDivision facade."""

from __future__ import annotations

import pytest

from careeros_offer_negotiation import Offer, OfferNegotiationDivision


@pytest.fixture
def division(offer_repository):
    return OfferNegotiationDivision(offer_repository)


def test_add_and_evaluate_offer(division, offer):
    division.add_offer(offer)
    breakdown = division.evaluate(offer.id)
    assert breakdown.offer_id == offer.id


def test_compare_all_ranks_saved_offers(division, offer):
    lower = Offer(company_name="Lower Co", job_title="Engineer", base_salary=50_000)
    division.add_offer(offer)
    division.add_offer(lower)
    ranked = division.compare_all()
    assert ranked[0].offer.id == offer.id


def test_negotiation_talking_points_delegates(division, offer):
    division.add_offer(offer)
    points = division.negotiation_talking_points(offer.id, target_base_salary=160_000)
    assert len(points) > 0


def test_negotiation_script_delegates(division, offer):
    division.add_offer(offer)
    script = division.negotiation_script(offer.id, target_base_salary=160_000)
    assert offer.company_name in script
