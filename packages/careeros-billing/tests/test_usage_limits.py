"""Tests for can_add_workspace / can_add_team_member."""

from __future__ import annotations

from careeros_billing import PlanTier, can_add_team_member, can_add_workspace


def test_free_tier_cannot_add_a_second_workspace():
    assert can_add_workspace(PlanTier.FREE, 1) is False


def test_free_tier_can_add_its_first_workspace():
    assert can_add_workspace(PlanTier.FREE, 0) is True


def test_agency_tier_can_add_workspaces_up_to_its_limit():
    assert can_add_workspace(PlanTier.AGENCY, 9) is True
    assert can_add_workspace(PlanTier.AGENCY, 10) is False


def test_free_tier_cannot_add_a_second_team_member():
    assert can_add_team_member(PlanTier.FREE, 1) is False


def test_agency_tier_can_add_team_members_up_to_its_limit():
    assert can_add_team_member(PlanTier.AGENCY, 24) is True
    assert can_add_team_member(PlanTier.AGENCY, 25) is False
