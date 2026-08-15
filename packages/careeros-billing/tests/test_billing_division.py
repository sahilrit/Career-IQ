"""Tests for the BillingDivision facade."""

from __future__ import annotations

import pytest

from careeros_billing import (
    BillingDivision,
    PlanTier,
    SubscriptionNotFoundError,
    SubscriptionStatus,
)


@pytest.fixture
def division(subscription_repository):
    return BillingDivision(subscription_repository)


def test_create_subscription_and_current_plan(division):
    division.create_subscription("workspace-1", PlanTier.PRO)
    assert division.current_plan("workspace-1").tier == PlanTier.PRO


def test_current_plan_raises_when_no_subscription(division):
    with pytest.raises(SubscriptionNotFoundError):
        division.current_plan("missing")


def test_is_feature_enabled_reflects_the_workspaces_plan(division):
    division.create_subscription("workspace-1", PlanTier.FREE)
    assert division.is_feature_enabled("workspace-1", "autonomous_workflows") is False
    division.upgrade("workspace-1", PlanTier.PRO)
    assert division.is_feature_enabled("workspace-1", "autonomous_workflows") is True


def test_can_add_workspace_reflects_the_plans_limit(division):
    division.create_subscription("workspace-1", PlanTier.FREE)
    assert division.can_add_workspace("workspace-1", 1) is False
    division.upgrade("workspace-1", PlanTier.AGENCY)
    assert division.can_add_workspace("workspace-1", 1) is True


def test_can_add_team_member_reflects_the_plans_limit(division):
    division.create_subscription("workspace-1", PlanTier.PRO)
    assert division.can_add_team_member("workspace-1", 1) is False


def test_cancel_sets_status_to_canceled(division):
    division.create_subscription("workspace-1", PlanTier.PRO)
    canceled = division.cancel("workspace-1")
    assert canceled.status == SubscriptionStatus.CANCELED
