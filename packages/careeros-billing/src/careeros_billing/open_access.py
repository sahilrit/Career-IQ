"""Open access: CareerOS is free for all right now.

We want usage data before we want revenue, so every workspace gets every
feature regardless of the tier recorded against it. Rather than delete
the plan model — which we would only have to rebuild once we know what
people actually pay for — this is a single switch that every gate reads.

Set ``CAREEROS_OPEN_ACCESS=0`` to fall back to real tier enforcement.
Subscriptions, Stripe webhooks and plan records keep working untouched
while the switch is on; they just stop deciding anything.
"""

from __future__ import annotations

import os

from careeros_billing.plan import PlanTier

OPEN_ACCESS_ENV_VAR = "CAREEROS_OPEN_ACCESS"

#: The tier every workspace is treated as while open access is on. Agency
#: rather than a bespoke "unlimited" tier, so limits stay finite and a
#: runaway caller still hits a ceiling.
OPEN_ACCESS_TIER = PlanTier.AGENCY

_FALSEY = {"0", "false", "no", "off", ""}


def open_access_enabled() -> bool:
    """True unless ``CAREEROS_OPEN_ACCESS`` is explicitly switched off.

    Defaults to on: an operator who has never heard of this variable gets
    the free-for-all behaviour we currently want, and turning charging
    back on is a deliberate act.
    """
    raw = os.environ.get(OPEN_ACCESS_ENV_VAR)
    if raw is None:
        return True
    return raw.strip().lower() not in _FALSEY


def effective_tier(tier: PlanTier) -> PlanTier:
    """The tier to actually enforce against, honouring open access.

    Every gate routes through this instead of reading ``subscription.plan_tier``
    directly, so there is exactly one place that knows about the override.
    """
    return OPEN_ACCESS_TIER if open_access_enabled() else tier
