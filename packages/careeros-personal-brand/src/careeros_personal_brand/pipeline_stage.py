"""ContentProgress: tracks how far one project's content has moved
through Project -> Case Study -> Portfolio -> LinkedIn Post -> X Thread
-> Blog -> Resume Achievement, mirroring
careeros_employment_division.PipelineProgress (Phase 30) and
careeros_client_acquisition.ClientAcquisitionProgress (Phase 31).
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "content_progress"


class ContentStage(StrEnum):
    CASE_STUDY = "case_study"
    PORTFOLIO = "portfolio"
    LINKEDIN_POST = "linkedin_post"
    X_THREAD = "x_thread"
    BLOG = "blog"
    RESUME_ACHIEVEMENT = "resume_achievement"


_STAGE_ORDER = list(ContentStage)


class ContentProgress(BaseModel):
    project_id: str
    completed_stages: list[ContentStage] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def current_stage(self) -> ContentStage | None:
        completed_set = set(self.completed_stages)
        current = None
        for stage in _STAGE_ORDER:
            if stage in completed_set:
                current = stage
        return current

    @property
    def next_stage(self) -> ContentStage | None:
        current = self.current_stage
        if current is None:
            return _STAGE_ORDER[0]
        index = _STAGE_ORDER.index(current)
        if index + 1 >= len(_STAGE_ORDER):
            return None
        return _STAGE_ORDER[index + 1]


class ContentProgressRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def load(self, project_id: str) -> ContentProgress:
        data = self._store.get_or_none(_ENTITY_TYPE, project_id)
        if data is None:
            return ContentProgress(project_id=project_id)
        return ContentProgress.model_validate(data)

    def mark_complete(self, project_id: str, stage: ContentStage) -> ContentProgress:
        progress = self.load(project_id)
        if stage not in progress.completed_stages:
            progress.completed_stages.append(stage)
        progress.updated_at = datetime.now(UTC)
        self._store.put(_ENTITY_TYPE, project_id, progress.model_dump(mode="json"))
        return progress
