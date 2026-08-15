"""Billing glue for the dashboard, kept Streamlit-free so it's testable:
resolve a workspace's subscription (defaulting to Free), and read the
checkout links for paid tiers from the environment.

Checkout uses Stripe Payment Links — plain URLs, no SDK, no secret key
in the app — honoring the platform's "no mandatory paid dependency"
constraint. After a customer pays, an admin activates the plan on the
Admin page (or a webhook-driven activator can be plugged in later).
"""

from __future__ import annotations

import os

from careeros_billing import PLANS, Plan, PlanTier, Subscription, SubscriptionRepository
from careeros_common import DocumentStore

_CHECKOUT_ENV = {
    PlanTier.PRO: "CAREEROS_STRIPE_LINK_PRO",
    PlanTier.AGENCY: "CAREEROS_STRIPE_LINK_AGENCY",
}


def current_subscription(raw_store: DocumentStore, workspace_id: str) -> Subscription:
    subscription = SubscriptionRepository(raw_store).load_or_none(workspace_id)
    if subscription is None:
        subscription = Subscription(workspace_id=workspace_id, plan_tier=PlanTier.FREE)
    return subscription


def current_plan(raw_store: DocumentStore, workspace_id: str) -> Plan:
    return PLANS[current_subscription(raw_store, workspace_id).plan_tier]


def checkout_link(tier: PlanTier) -> str | None:
    env_name = _CHECKOUT_ENV.get(tier)
    return os.environ.get(env_name) or None if env_name else None


def set_plan(raw_store: DocumentStore, workspace_id: str, tier: PlanTier) -> Subscription:
    """Admin-side activation: move a workspace onto a tier."""
    subscription = current_subscription(raw_store, workspace_id)
    subscription.plan_tier = tier
    SubscriptionRepository(raw_store).save(subscription)
    return subscription
