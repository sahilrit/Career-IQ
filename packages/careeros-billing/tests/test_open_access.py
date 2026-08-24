"""Tests for open-access mode — CareerOS free for all.

These exercise the switch itself. The tier-specific tests in
``test_feature_gate.py`` and ``test_usage_limits.py`` pin open access off
so they keep testing the plan model rather than the override.
"""

from __future__ import annotations

import pytest

from careeros_billing import PlanTier, is_feature_enabled
from careeros_billing.open_access import (
    OPEN_ACCESS_ENV_VAR,
    OPEN_ACCESS_TIER,
    effective_tier,
    open_access_enabled,
)
from careeros_billing.usage_limits import can_add_team_member, can_add_workspace


def test_open_access_is_on_by_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv(OPEN_ACCESS_ENV_VAR, raising=False)
    assert open_access_enabled() is True


@pytest.mark.parametrize("value", ["0", "false", "FALSE", "no", "off", ""])
def test_open_access_can_be_switched_off(monkeypatch: pytest.MonkeyPatch, value: str):
    monkeypatch.setenv(OPEN_ACCESS_ENV_VAR, value)
    assert open_access_enabled() is False


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_open_access_accepts_the_usual_truthy_spellings(
    monkeypatch: pytest.MonkeyPatch, value: str
):
    monkeypatch.setenv(OPEN_ACCESS_ENV_VAR, value)
    assert open_access_enabled() is True


def test_effective_tier_upgrades_every_tier_while_open(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(OPEN_ACCESS_ENV_VAR, "1")
    for tier in PlanTier:
        assert effective_tier(tier) is OPEN_ACCESS_TIER


def test_effective_tier_is_a_passthrough_when_closed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(OPEN_ACCESS_ENV_VAR, "0")
    for tier in PlanTier:
        assert effective_tier(tier) is tier


def test_free_workspaces_get_every_paid_feature(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(OPEN_ACCESS_ENV_VAR, "1")
    for feature in ("autonomous_workflows", "interview_intelligence", "api_access"):
        assert is_feature_enabled(PlanTier.FREE, feature) is True


def test_open_access_still_rejects_features_that_do_not_exist(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(OPEN_ACCESS_ENV_VAR, "1")
    assert is_feature_enabled(PlanTier.FREE, "not_a_real_feature") is False


def test_free_workspaces_get_agency_seat_and_workspace_limits(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(OPEN_ACCESS_ENV_VAR, "1")
    assert can_add_workspace(PlanTier.FREE, current_workspace_count=5) is True
    assert can_add_team_member(PlanTier.FREE, current_team_member_count=10) is True


def test_open_access_limits_are_still_finite(monkeypatch: pytest.MonkeyPatch):
    """Free for all, not unbounded — the Agency ceiling still applies, so a
    runaway loop can't create workspaces forever."""
    monkeypatch.setenv(OPEN_ACCESS_ENV_VAR, "1")
    assert can_add_workspace(PlanTier.FREE, current_workspace_count=10) is False
    assert can_add_team_member(PlanTier.FREE, current_team_member_count=25) is False
