"""Admin endpoints: customer overview + MRR, and manual plan activation.
Restricted to operators (CAREEROS_ADMIN_EMAILS)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from careeros_api.dependencies import Context
from careeros_api.schemas import (
    ActivatePlanRequest,
    AdminOverviewResponse,
    CustomerResponse,
)
from careeros_billing import PLANS, PlanTier, Subscription, SubscriptionRepository
from careeros_tenancy import TenancyRepository

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(context: Context) -> None:
    if not context.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin access required")


@router.get("/overview", response_model=AdminOverviewResponse)
def overview(context: Context) -> AdminOverviewResponse:
    _require_admin(context)
    tenancy = TenancyRepository(context.raw_store)
    subscriptions = SubscriptionRepository(context.raw_store)
    users = tenancy.list_users()

    customers: list[CustomerResponse] = []
    for user in users:
        for membership in tenancy.workspaces_for_user(user.id):
            subscription = subscriptions.load_or_none(membership.workspace_id) or Subscription(
                workspace_id=membership.workspace_id, plan_tier=PlanTier.FREE
            )
            customers.append(
                CustomerResponse(
                    name=user.full_name,
                    email=user.email,
                    role=membership.role.value,
                    workspace_id=membership.workspace_id,
                    plan=subscription.plan_tier.value,
                    status=subscription.status.value,
                    joined=f"{user.created_at:%Y-%m-%d}",
                )
            )

    paying = [c for c in customers if c.plan != PlanTier.FREE.value]
    mrr = sum(PLANS[PlanTier(c.plan)].monthly_price_usd for c in paying)
    return AdminOverviewResponse(
        accounts=len(users),
        paying_workspaces=len(paying),
        mrr=mrr,
        customers=customers,
    )


@router.post("/activate", response_model=AdminOverviewResponse)
def activate(body: ActivatePlanRequest, context: Context) -> AdminOverviewResponse:
    _require_admin(context)
    try:
        tier = PlanTier(body.tier)
    except ValueError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "unknown tier") from error
    subscriptions = SubscriptionRepository(context.raw_store)
    subscription = subscriptions.load_or_none(body.workspace_id) or Subscription(
        workspace_id=body.workspace_id, plan_tier=tier
    )
    subscription.plan_tier = tier
    subscriptions.save(subscription)
    return overview(context)
