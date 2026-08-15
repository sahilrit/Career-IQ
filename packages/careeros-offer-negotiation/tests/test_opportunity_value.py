"""Tests for calculate_opportunity_value."""

from __future__ import annotations

from careeros_offer_negotiation import DISCLAIMER, Offer, calculate_opportunity_value


def test_pretax_total_sums_every_component(offer):
    breakdown = calculate_opportunity_value(offer)
    assert breakdown.pretax_total == 150_000 + 10_000 + 20_000 + 15_000


def test_no_tax_rate_means_after_tax_equals_pretax(offer):
    breakdown = calculate_opportunity_value(offer)
    assert breakdown.after_tax_total == breakdown.pretax_total


def test_tax_rate_reduces_after_tax_total(offer):
    breakdown = calculate_opportunity_value(offer, effective_tax_rate=0.25)
    assert breakdown.after_tax_total == breakdown.pretax_total * 0.75


def test_no_qualitative_scores_gives_neutral_multiplier(offer):
    breakdown = calculate_opportunity_value(offer)
    assert breakdown.qualitative_multiplier == 1.0
    assert breakdown.opportunity_value == breakdown.after_tax_total


def test_above_average_scores_raise_the_multiplier():
    offer = Offer(
        company_name="Acme",
        job_title="Engineer",
        base_salary=100_000,
        stability_score=5,
        growth_score=5,
        reputation_score=5,
    )
    breakdown = calculate_opportunity_value(offer)
    assert breakdown.qualitative_multiplier > 1.0
    assert breakdown.opportunity_value > breakdown.after_tax_total


def test_below_average_scores_lower_the_multiplier():
    offer = Offer(
        company_name="Acme",
        job_title="Engineer",
        base_salary=100_000,
        stability_score=1,
        growth_score=1,
        reputation_score=1,
    )
    breakdown = calculate_opportunity_value(offer)
    assert breakdown.qualitative_multiplier < 1.0
    assert breakdown.opportunity_value < breakdown.after_tax_total


def test_disclaimer_is_present(offer):
    breakdown = calculate_opportunity_value(offer)
    assert breakdown.disclaimer == DISCLAIMER
