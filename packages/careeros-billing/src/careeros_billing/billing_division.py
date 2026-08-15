"""BillingDivision: the facade tying plans, subscriptions, feature
gating, and usage limits together. Never touches real money — a real
payment processor would plug in as an optional provider that calls
into this state layer via webhooks, exactly like every other paid
integration in CareerOS is optional and pluggable.
"""

from __future__ import annotations

from careeros_billing.exceptions import SubscriptionNotFoundError
from careeros_billing.feature_gate import is_feature_enabled
from careeros_billing.plan import Plan, PlanTier, get_plan
from careeros_billing.subscription import Subscription, SubscriptionRepository, SubscriptionStatus
from careeros_billing.usage_limits import can_add_team_member, can_add_workspace


class BillingDivision:
    def __init__(self, subscription_repository: SubscriptionRepository) -> None:
        self._subscriptions = subscription_repository

    def create_subscription(self, workspace_id: str, tier: PlanTier) -> Subscription:
        subscription = Subscription(workspace_id=workspace_id, plan_tier=tier)
        self._subscriptions.save(subscription)
        return subscription

    def _require_subscription(self, workspace_id: str) -> Subscription:
        subscription = self._subscriptions.load_or_none(workspace_id)
        if subscription is None:
            raise SubscriptionNotFoundError(f"No subscription for workspace {workspace_id!r}")
        return subscription

    def current_plan(self, workspace_id: str) -> Plan:
        return get_plan(self._require_subscription(workspace_id).plan_tier)

    def is_feature_enabled(self, workspace_id: str, feature: str) -> bool:
        return is_feature_enabled(self._require_subscription(workspace_id).plan_tier, feature)

    def can_add_workspace(self, workspace_id: str, current_workspace_count: int) -> bool:
        tier = self._require_subscription(workspace_id).plan_tier
        return can_add_workspace(tier, current_workspace_count)

    def can_add_team_member(self, workspace_id: str, current_team_member_count: int) -> bool:
        tier = self._require_subscription(workspace_id).plan_tier
        return can_add_team_member(tier, current_team_member_count)

    def upgrade(self, workspace_id: str, new_tier: PlanTier) -> Subscription:
        subscription = self._require_subscription(workspace_id)
        subscription.plan_tier = new_tier
        self._subscriptions.save(subscription)
        return subscription

    def cancel(self, workspace_id: str) -> Subscription:
        subscription = self._require_subscription(workspace_id)
        subscription.status = SubscriptionStatus.CANCELED
        self._subscriptions.save(subscription)
        return subscription
