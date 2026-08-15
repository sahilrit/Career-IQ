"""Tests for Subscription / SubscriptionRepository."""

from __future__ import annotations

from careeros_billing import PlanTier, Subscription, SubscriptionStatus


def test_save_and_load_round_trips(subscription_repository):
    subscription = Subscription(workspace_id="workspace-1", plan_tier=PlanTier.PRO)
    subscription_repository.save(subscription)
    assert subscription_repository.load_or_none("workspace-1") == subscription


def test_load_or_none_returns_none_when_missing(subscription_repository):
    assert subscription_repository.load_or_none("missing") is None


def test_default_status_is_active():
    subscription = Subscription(workspace_id="workspace-1", plan_tier=PlanTier.FREE)
    assert subscription.status == SubscriptionStatus.ACTIVE


def test_saving_again_overwrites_the_prior_record(subscription_repository):
    subscription_repository.save(Subscription(workspace_id="workspace-1", plan_tier=PlanTier.FREE))
    subscription_repository.save(Subscription(workspace_id="workspace-1", plan_tier=PlanTier.PRO))
    assert subscription_repository.load_or_none("workspace-1").plan_tier == PlanTier.PRO
