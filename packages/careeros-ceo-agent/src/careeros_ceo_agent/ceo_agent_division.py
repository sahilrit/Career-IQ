"""CEOAgentDivision: the facade recording performance evidence,
computing a resource allocation from it, and keeping the history of
every plan so far.
"""

from __future__ import annotations

from careeros_ceo_agent.allocation import DEFAULT_BASELINE, AllocationPlan, allocate_resources
from careeros_ceo_agent.allocation_history import AllocationPlanRepository
from careeros_ceo_agent.performance_input import (
    PerformanceInput,
    PerformanceInputRepository,
    ResourceCategory,
)


class CEOAgentDivision:
    def __init__(
        self,
        performance_repository: PerformanceInputRepository,
        plan_repository: AllocationPlanRepository,
    ) -> None:
        self._performance = performance_repository
        self._plans = plan_repository

    def record_performance(self, performance_input: PerformanceInput) -> None:
        self._performance.save(performance_input)

    def compute_allocation(
        self,
        *,
        baseline: dict[ResourceCategory, float] | None = None,
        shift_weight: float = 0.5,
    ) -> AllocationPlan:
        plan = allocate_resources(
            self._performance.list_all(),
            baseline=baseline or DEFAULT_BASELINE,
            shift_weight=shift_weight,
        )
        self._plans.save(plan)
        return plan

    def allocation_history(self) -> list[AllocationPlan]:
        return self._plans.list_all()

    def latest_allocation(self) -> AllocationPlan | None:
        history = self.allocation_history()
        return history[-1] if history else None
