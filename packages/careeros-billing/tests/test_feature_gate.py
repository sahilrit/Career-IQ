"""Tests for is_feature_enabled."""

from __future__ import annotations

from careeros_billing import PlanTier, is_feature_enabled


def test_free_tier_has_career_brain():
    assert is_feature_enabled(PlanTier.FREE, "career_brain") is True


def test_free_tier_does_not_have_autonomous_workflows():
    assert is_feature_enabled(PlanTier.FREE, "autonomous_workflows") is False


def test_pro_tier_has_autonomous_workflows():
    assert is_feature_enabled(PlanTier.PRO, "autonomous_workflows") is True


def test_pro_tier_does_not_have_multiple_workspaces():
    assert is_feature_enabled(PlanTier.PRO, "multiple_workspaces") is False


def test_agency_tier_has_multiple_workspaces():
    assert is_feature_enabled(PlanTier.AGENCY, "multiple_workspaces") is True


def test_unknown_feature_is_disabled_everywhere():
    assert is_feature_enabled(PlanTier.AGENCY, "not_a_real_feature") is False
