"""Tests for compare_offers."""

from __future__ import annotations

from careeros_offer_negotiation import Offer, compare_offers


def test_ranks_higher_opportunity_value_first():
    high = Offer(company_name="High Co", job_title="Engineer", base_salary=200_000)
    low = Offer(company_name="Low Co", job_title="Engineer", base_salary=100_000)
    ranked = compare_offers([low, high])
    assert [r.offer.company_name for r in ranked] == ["High Co", "Low Co"]


def test_empty_list_returns_empty():
    assert compare_offers([]) == []


def test_tax_rate_is_applied_to_every_offer():
    offer_a = Offer(company_name="A", job_title="Engineer", base_salary=100_000)
    offer_b = Offer(company_name="B", job_title="Engineer", base_salary=100_000)
    ranked = compare_offers([offer_a, offer_b], effective_tax_rate=0.2)
    assert all(r.breakdown.after_tax_total == 80_000 for r in ranked)
