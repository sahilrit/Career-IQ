"""CEO Agent: log results across your work streams and get a suggested
effort allocation across them (guidance only, never financial advice)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from careeros_api.dependencies import Context
from careeros_ceo_agent import (
    AllocationPlanRepository,
    CEOAgentDivision,
    PerformanceInput,
    PerformanceInputRepository,
    ResourceCategory,
)

router = APIRouter(prefix="/ceo", tags=["ceo"])


class PerformanceRequest(BaseModel):
    category: str = Field(min_length=1)
    metric_name: str = Field(min_length=1)
    value: float


def _division(context: Context) -> CEOAgentDivision:
    return CEOAgentDivision(
        PerformanceInputRepository(context.store), AllocationPlanRepository(context.store)
    )


def _plan_json(plan: Any) -> dict[str, Any] | None:
    if plan is None:
        return None
    return {
        "allocations": {category.value: pct for category, pct in plan.allocations.items()},
        "generated_at": plan.generated_at.isoformat(),
        "disclaimer": plan.disclaimer,
    }


@router.get("")
def overview(context: Context) -> dict[str, Any]:
    division = _division(context)
    return {
        "latest": _plan_json(division.latest_allocation()),
        "history": [_plan_json(plan) for plan in division.allocation_history()],
    }


@router.post("/performance", status_code=status.HTTP_201_CREATED)
def record(body: PerformanceRequest, context: Context) -> dict[str, Any]:
    try:
        category = ResourceCategory(body.category)
    except ValueError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "unknown category") from error
    _division(context).record_performance(
        PerformanceInput(
            category=category, metric_name=body.metric_name, value=body.value, source="web"
        )
    )
    return {"ok": True}


@router.post("/compute")
def compute(context: Context) -> dict[str, Any]:
    plan = _division(context).compute_allocation()
    return _plan_json(plan) or {}
