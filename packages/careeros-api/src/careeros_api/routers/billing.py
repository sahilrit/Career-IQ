"""Billing endpoint: the workspace's current plan and every tier, with
Stripe Payment Link checkout URLs for upgrades."""

from __future__ import annotations

import os

from fastapi import APIRouter

from careeros_api.dependencies import Context
from careeros_api.schemas import BillingResponse, PlanInfo
from careeros_billing import PLANS, PlanTier, Subscription, SubscriptionRepository

router = APIRouter(prefix="/billing", tags=["billing"])

_CHECKOUT_ENV = {
    PlanTier.PRO: "CAREEROS_STRIPE_LINK_PRO",
    PlanTier.AGENCY: "CAREEROS_STRIPE_LINK_AGENCY",
}


def _checkout_url(tier: PlanTier) -> str | None:
    env_name = _CHECKOUT_ENV.get(tier)
    return (os.environ.get(env_name) or None) if env_name else None


@router.get("", response_model=BillingResponse)
def get_billing(context: Context) -> BillingResponse:
    subscription = SubscriptionRepository(context.raw_store).load_or_none(
        context.account.workspace_id
    ) or Subscription(workspace_id=context.account.workspace_id, plan_tier=PlanTier.FREE)
    current = subscription.plan_tier
    current_price = PLANS[current].monthly_price_usd

    plans = [
        PlanInfo(
            tier=tier.value,
            name=plan.name,
            monthly_price_usd=plan.monthly_price_usd,
            features=plan.features,
            is_current=tier == current,
            # Only offer checkout for a strictly higher tier than the current one.
            checkout_url=(_checkout_url(tier) if plan.monthly_price_usd > current_price else None),
        )
        for tier, plan in PLANS.items()
    ]
    return BillingResponse(
        current_tier=current.value, status=subscription.status.value, plans=plans
    )
