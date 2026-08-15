"""PredictionProgress: tracks how far one predicted-demand company has
moved through the roadmap's chain:

    Signal detected -> Demand predicted -> Researched
      -> Decision maker identified -> Relationship started -> Positioned

Same furthest-reached pattern as Phase 30/31/34's pipeline progress.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "prediction_progress"


class PredictionStage(StrEnum):
    SIGNAL_DETECTED = "signal_detected"
    DEMAND_PREDICTED = "demand_predicted"
    RESEARCHED = "researched"
    DECISION_MAKER_IDENTIFIED = "decision_maker_identified"
    RELATIONSHIP_STARTED = "relationship_started"
    POSITIONED = "positioned"


_STAGE_ORDER = list(PredictionStage)


class PredictionProgress(BaseModel):
    company_id: str
    completed_stages: list[PredictionStage] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def current_stage(self) -> PredictionStage | None:
        completed_set = set(self.completed_stages)
        current = None
        for stage in _STAGE_ORDER:
            if stage in completed_set:
                current = stage
        return current

    @property
    def next_stage(self) -> PredictionStage | None:
        current = self.current_stage
        if current is None:
            return _STAGE_ORDER[0]
        index = _STAGE_ORDER.index(current)
        if index + 1 >= len(_STAGE_ORDER):
            return None
        return _STAGE_ORDER[index + 1]


class PredictionProgressRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def load(self, company_id: str) -> PredictionProgress:
        data = self._store.get_or_none(_ENTITY_TYPE, company_id)
        if data is None:
            return PredictionProgress(company_id=company_id)
        return PredictionProgress.model_validate(data)

    def mark_complete(self, company_id: str, stage: PredictionStage) -> PredictionProgress:
        progress = self.load(company_id)
        if stage not in progress.completed_stages:
            progress.completed_stages.append(stage)
        progress.updated_at = datetime.now(UTC)
        self._store.put(_ENTITY_TYPE, company_id, progress.model_dump(mode="json"))
        return progress
