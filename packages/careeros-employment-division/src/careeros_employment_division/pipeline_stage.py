"""PipelineProgress: tracks which Employment Division artifacts have
been generated for one application — separate from Career Brain's
``Application.status`` (Phase 2), which tracks real-world state (has the
employer responded), not CareerOS's own internal preparation progress.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "pipeline_progress"


class PipelineStage(StrEnum):
    DISCOVERY = "discovery"
    SCORING = "scoring"
    RESEARCH = "research"
    RESUME = "resume"
    PORTFOLIO = "portfolio"
    COVER_LETTER = "cover_letter"
    RECRUITER_OUTREACH = "recruiter_outreach"
    APPLICATION = "application"
    FOLLOW_UP = "follow_up"
    INTERVIEW = "interview"
    OFFER = "offer"
    NEGOTIATION = "negotiation"


_STAGE_ORDER = list(PipelineStage)


class PipelineProgress(BaseModel):
    application_id: str
    completed_stages: list[PipelineStage] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def current_stage(self) -> PipelineStage | None:
        """The furthest stage reached, or None if nothing's been done yet."""
        completed_set = set(self.completed_stages)
        current = None
        for stage in _STAGE_ORDER:
            if stage in completed_set:
                current = stage
        return current

    @property
    def next_stage(self) -> PipelineStage | None:
        current = self.current_stage
        if current is None:
            return _STAGE_ORDER[0]
        index = _STAGE_ORDER.index(current)
        if index + 1 >= len(_STAGE_ORDER):
            return None
        return _STAGE_ORDER[index + 1]


class PipelineProgressRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def load(self, application_id: str) -> PipelineProgress:
        data = self._store.get_or_none(_ENTITY_TYPE, application_id)
        if data is None:
            return PipelineProgress(application_id=application_id)
        return PipelineProgress.model_validate(data)

    def mark_complete(self, application_id: str, stage: PipelineStage) -> PipelineProgress:
        progress = self.load(application_id)
        if stage not in progress.completed_stages:
            progress.completed_stages.append(stage)
        progress.updated_at = datetime.now(UTC)
        self._store.put(_ENTITY_TYPE, application_id, progress.model_dump(mode="json"))
        return progress
