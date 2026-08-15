"""Tests for generate_negotiation_talking_points / render_negotiation_script."""

from __future__ import annotations

from careeros_offer_negotiation import (
    Offer,
    generate_negotiation_talking_points,
    render_negotiation_script,
)


def test_gap_above_target_generates_an_ask(offer):
    points = generate_negotiation_talking_points(offer, target_base_salary=160_000)
    assert any("$10,000" in point for point in points)


def test_no_gap_suggests_focusing_on_other_levers(offer):
    points = generate_negotiation_talking_points(offer, target_base_salary=140_000)
    assert any("other levers" in point for point in points)


def test_zero_bonus_is_flagged():
    offer = Offer(company_name="Acme", job_title="Engineer", base_salary=100_000)
    points = generate_negotiation_talking_points(offer, target_base_salary=100_000)
    assert any("signing bonus" in point for point in points)


def test_zero_equity_is_flagged():
    offer = Offer(company_name="Acme", job_title="Engineer", base_salary=100_000)
    points = generate_negotiation_talking_points(offer, target_base_salary=100_000)
    assert any("equity" in point for point in points)


def test_low_pto_is_flagged():
    offer = Offer(company_name="Acme", job_title="Engineer", base_salary=100_000, pto_days=10)
    points = generate_negotiation_talking_points(offer, target_base_salary=100_000)
    assert any("PTO" in point for point in points)


def test_generous_pto_is_not_flagged():
    offer = Offer(company_name="Acme", job_title="Engineer", base_salary=100_000, pto_days=25)
    points = generate_negotiation_talking_points(offer, target_base_salary=100_000)
    assert not any("PTO" in point for point in points)


def test_script_mentions_company_and_title(offer):
    script = render_negotiation_script(offer, target_base_salary=160_000)
    assert offer.company_name in script
    assert offer.job_title in script
