"""Feature gating: a pure lookup against a plan's real feature list —
no separate configuration to drift out of sync with the plan
definitions themselves.

While open access is on (the default — see ``open_access``), the lookup
runs against the Agency feature list no matter which tier is passed in,
so everything is unlocked for everyone.
"""

from __future__ import annotations

from careeros_billing.open_access import effective_tier
from careeros_billing.plan import PlanTier, get_plan


def is_feature_enabled(tier: PlanTier, feature: str) -> bool:
    return feature in get_plan(effective_tier(tier)).features
