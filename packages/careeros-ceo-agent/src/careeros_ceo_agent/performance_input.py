"""PerformanceInput: real, sourced evidence of how one division
(Employment, Freelance, Networking, Personal Brand) is actually
performing — response rates from Learning Lab, revenue from Financial
Intelligence, demand scores from Opportunity Prediction, and so on.

This package is a pure combinator, the same design as Phase 40's
Career Intelligence Engine: it doesn't compute performance itself, it
allocates resources from performance numbers the rest of the platform
already produced. ``source`` keeps every allocation traceable back to
real evidence.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "performance_input"


class ResourceCategory(StrEnum):
    EMPLOYMENT = "employment"
    FREELANCE = "freelance"
    NETWORKING = "networking"
    PERSONAL_BRAND = "personal_brand"


class PerformanceInput(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: ResourceCategory
    metric_name: str
    value: float
    source: str
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PerformanceInputRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, performance_input: PerformanceInput) -> None:
        self._store.put(
            _ENTITY_TYPE, performance_input.id, performance_input.model_dump(mode="json")
        )

    def list_all(self) -> list[PerformanceInput]:
        return [PerformanceInput.model_validate(data) for data in self._store.list(_ENTITY_TYPE)]
