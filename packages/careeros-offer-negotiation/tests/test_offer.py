"""Tests for Offer / OfferRepository."""

from __future__ import annotations

from careeros_offer_negotiation import Offer


def test_save_and_load_round_trips(offer_repository, offer):
    offer_repository.save(offer)
    assert offer_repository.load(offer.id) == offer


def test_load_or_none_returns_none_when_missing(offer_repository):
    assert offer_repository.load_or_none("missing") is None


def test_list_all_returns_every_saved_offer(offer_repository, offer):
    offer_repository.save(offer)
    assert offer_repository.list_all() == [offer]


def test_defaults_are_zero_or_empty():
    offer = Offer(company_name="Acme", job_title="Engineer", base_salary=100_000)
    assert offer.bonus == 0.0
    assert offer.equity_value == 0.0
    assert offer.benefits_value == 0.0
    assert offer.pto_days == 0
