"""Feature gating: a pure lookup against a plan's real feature list —
no separate configuration to drift out of sync with the plan
definitions themselves.
"""

from __future__ import annotations

from careeros_billing.plan import PlanTier, get_plan


def is_feature_enabled(tier: PlanTier, feature: str) -> bool:
    return feature in get_plan(tier).features
