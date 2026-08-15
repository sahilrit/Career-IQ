"""careeros_billing: SaaS Billing & Plans.

The Free/Pro/Agency plan model, feature gating, subscription state
tracking, and usage limits — a monetization layer, never a dependency
of the core platform. No real payment processor is integrated; that
would plug in as an optional provider behind this state-tracking layer,
the same "pluggable, never mandatory" pattern every paid integration in
CareerOS follows.
"""

from careeros_billing.billing_division import BillingDivision
from careeros_billing.exceptions import BillingError, SubscriptionNotFoundError
from careeros_billing.feature_gate import is_feature_enabled
from careeros_billing.plan import PLANS, Plan, PlanTier, get_plan
from careeros_billing.subscription import Subscription, SubscriptionRepository, SubscriptionStatus
from careeros_billing.usage_limits import can_add_team_member, can_add_workspace

__all__ = [
    "PLANS",
    "BillingDivision",
    "BillingError",
    "Plan",
    "PlanTier",
    "Subscription",
    "SubscriptionNotFoundError",
    "SubscriptionRepository",
    "SubscriptionStatus",
    "can_add_team_member",
    "can_add_workspace",
    "get_plan",
    "is_feature_enabled",
]
