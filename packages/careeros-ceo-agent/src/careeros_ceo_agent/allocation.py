"""Resource allocation: a transparent, evidence-weighted blend of a
baseline split and real recorded performance — not a hidden "strategic
AI judgment" black box. With no performance evidence at all, the
allocation is exactly the baseline; each unit of real evidence shifts
it, capped by ``shift_weight`` so a single data point can't swing the
whole plan.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from careeros_ceo_agent.performance_input import PerformanceInput, ResourceCategory

DISCLAIMER = (
    "Allocation is a transparent, evidence-weighted blend of baseline and recent "
    "performance — not a guarantee of future results."
)
_CATEGORIES = list(ResourceCategory)
_EQUAL_SHARE = 100.0 / len(_CATEGORIES)
DEFAULT_BASELINE: dict[ResourceCategory, float] = dict.fromkeys(_CATEGORIES, _EQUAL_SHARE)
_DEFAULT_SHIFT_WEIGHT = 0.5


class AllocationPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    allocations: dict[ResourceCategory, float]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    disclaimer: str = DISCLAIMER


def allocate_resources(
    performance_inputs: list[PerformanceInput],
    *,
    baseline: dict[ResourceCategory, float] | None = None,
    shift_weight: float = _DEFAULT_SHIFT_WEIGHT,
) -> AllocationPlan:
    base = baseline or DEFAULT_BASELINE

    performance_by_category: dict[ResourceCategory, float] = dict.fromkeys(_CATEGORIES, 0.0)
    for performance_input in performance_inputs:
        performance_by_category[performance_input.category] += performance_input.value

    total_performance = sum(performance_by_category.values())

    if total_performance <= 0:
        allocations = dict(base)
    else:
        allocations = {
            category: base.get(category, 0.0) * (1 - shift_weight)
            + (performance_by_category[category] / total_performance * 100) * shift_weight
            for category in _CATEGORIES
        }

    return AllocationPlan(allocations=_normalize_to_100(allocations))


def _normalize_to_100(
    allocations: dict[ResourceCategory, float],
) -> dict[ResourceCategory, float]:
    total = sum(allocations.values())
    if total <= 0:
        return dict(DEFAULT_BASELINE)
    return {category: value / total * 100 for category, value in allocations.items()}
