"""AllocationPlanRepository: stores every computed AllocationPlan, so
how the allocation actually moved as real results came in is visible,
not just the latest snapshot.
"""

from __future__ import annotations

from careeros_ceo_agent.allocation import AllocationPlan
from careeros_common import DocumentStore

_ENTITY_TYPE = "allocation_plan"


class AllocationPlanRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, plan: AllocationPlan) -> None:
        self._store.put(_ENTITY_TYPE, plan.id, plan.model_dump(mode="json"))

    def list_all(self) -> list[AllocationPlan]:
        plans = [AllocationPlan.model_validate(data) for data in self._store.list(_ENTITY_TYPE)]
        plans.sort(key=lambda plan: plan.generated_at)
        return plans
