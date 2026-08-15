"""Tests for DecisionMaker / DecisionMakerRepository."""

from __future__ import annotations

from careeros_opportunity_prediction import DecisionMaker


def test_list_for_company_filters(decision_maker_repository):
    matching = DecisionMaker(company_id="company-1", name="Jane Smith", title="VP Engineering")
    other = DecisionMaker(company_id="company-2", name="Bob Jones")
    decision_maker_repository.save(matching)
    decision_maker_repository.save(other)
    assert decision_maker_repository.list_for_company("company-1") == [matching]
