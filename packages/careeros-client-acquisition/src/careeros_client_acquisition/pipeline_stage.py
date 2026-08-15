"""ClientAcquisitionProgress: tracks how far one company prospect has
moved through the acquisition pipeline, mirroring
careeros_employment_division.PipelineProgress (Phase 30) but for the
company-acquisition stage sequence.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "client_acquisition_progress"


class ClientAcquisitionStage(StrEnum):
    DISCOVERY = "discovery"
    QUALIFICATION = "qualification"
    PROBLEM_DETECTION = "problem_detection"
    OPPORTUNITY_SCORE = "opportunity_score"
    AUDIT = "audit"
    OUTREACH = "outreach"
    FOLLOW_UP = "follow_up"
    PROPOSAL = "proposal"
    CALL = "call"
    CONTRACT = "contract"
    CLIENT = "client"


_STAGE_ORDER = list(ClientAcquisitionStage)


class ClientAcquisitionProgress(BaseModel):
    company_id: str
    completed_stages: list[ClientAcquisitionStage] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def current_stage(self) -> ClientAcquisitionStage | None:
        completed_set = set(self.completed_stages)
        current = None
        for stage in _STAGE_ORDER:
            if stage in completed_set:
                current = stage
        return current

    @property
    def next_stage(self) -> ClientAcquisitionStage | None:
        current = self.current_stage
        if current is None:
            return _STAGE_ORDER[0]
        index = _STAGE_ORDER.index(current)
        if index + 1 >= len(_STAGE_ORDER):
            return None
        return _STAGE_ORDER[index + 1]


class ClientAcquisitionProgressRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def load(self, company_id: str) -> ClientAcquisitionProgress:
        data = self._store.get_or_none(_ENTITY_TYPE, company_id)
        if data is None:
            return ClientAcquisitionProgress(company_id=company_id)
        return ClientAcquisitionProgress.model_validate(data)

    def mark_complete(
        self, company_id: str, stage: ClientAcquisitionStage
    ) -> ClientAcquisitionProgress:
        progress = self.load(company_id)
        if stage not in progress.completed_stages:
            progress.completed_stages.append(stage)
        progress.updated_at = datetime.now(UTC)
        self._store.put(_ENTITY_TYPE, company_id, progress.model_dump(mode="json"))
        return progress
