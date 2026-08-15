"""Tests for the plan definitions."""

from __future__ import annotations

from careeros_billing import PLANS, PlanTier, get_plan


def test_all_three_tiers_are_defined():
    assert set(PLANS) == {PlanTier.FREE, PlanTier.PRO, PlanTier.AGENCY}


def test_free_tier_is_free():
    assert get_plan(PlanTier.FREE).monthly_price_usd == 0.0


def test_pro_tier_includes_everything_free_has():
    free_features = set(get_plan(PlanTier.FREE).features)
    pro_features = set(get_plan(PlanTier.PRO).features)
    assert free_features <= pro_features


def test_agency_tier_includes_everything_pro_has():
    pro_features = set(get_plan(PlanTier.PRO).features)
    agency_features = set(get_plan(PlanTier.AGENCY).features)
    assert pro_features <= agency_features


def test_only_agency_supports_multiple_workspaces():
    assert get_plan(PlanTier.FREE).max_workspaces == 1
    assert get_plan(PlanTier.PRO).max_workspaces == 1
    assert get_plan(PlanTier.AGENCY).max_workspaces > 1
