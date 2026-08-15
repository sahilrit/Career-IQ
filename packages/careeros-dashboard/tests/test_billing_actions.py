"""Tests for the Streamlit-free billing glue."""

from __future__ import annotations

from careeros_billing import PlanTier, SubscriptionRepository
from careeros_dashboard.billing_actions import (
    checkout_link,
    current_plan,
    current_subscription,
    set_plan,
)


def test_workspace_without_subscription_defaults_to_free(store):
    subscription = current_subscription(store, "ws-1")
    assert subscription.plan_tier == PlanTier.FREE
    assert current_plan(store, "ws-1").monthly_price_usd == 0.0


def test_set_plan_persists_and_is_read_back(store):
    set_plan(store, "ws-1", PlanTier.PRO)
    assert current_subscription(store, "ws-1").plan_tier == PlanTier.PRO
    assert SubscriptionRepository(store).load_or_none("ws-1").plan_tier == PlanTier.PRO


def test_checkout_link_comes_from_the_environment(monkeypatch):
    monkeypatch.delenv("CAREEROS_STRIPE_LINK_PRO", raising=False)
    assert checkout_link(PlanTier.PRO) is None
    assert checkout_link(PlanTier.FREE) is None
    monkeypatch.setenv("CAREEROS_STRIPE_LINK_PRO", "https://buy.stripe.com/test")
    assert checkout_link(PlanTier.PRO) == "https://buy.stripe.com/test"
