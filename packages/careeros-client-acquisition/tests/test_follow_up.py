"""Tests for generate_follow_up_message."""

from __future__ import annotations

from careeros_client_acquisition import generate_follow_up_message


def test_mentions_company_name(company):
    message = generate_follow_up_message(company, days_since_outreach=3)
    assert company.name in message


def test_singular_day_grammar(company):
    message = generate_follow_up_message(company, days_since_outreach=1)
    assert "1 day " in message


def test_plural_days_grammar(company):
    message = generate_follow_up_message(company, days_since_outreach=5)
    assert "5 days " in message
