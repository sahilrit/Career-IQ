"""AgencyCycleProgress: tracks one user's real progress through the
roadmap's final loop —

    Employment / Freelance / Personal Brand -> Networking
      -> Client Success -> Financial Intelligence -> Career Intelligence
      -> CEO Agent -> Learning -> (loop back)

Same furthest-reached pattern as Phase 30/31/34/38/53's pipeline
progress. ``subject_id`` is meant to share Phase 2's Career Brain
identity id; this package only tracks the journey — it doesn't perform
any stage itself. Employment/Freelance/Networking are marked complete
automatically from real events already published elsewhere (see
``events.py``); the remaining stages have no platform event yet, so the
caller marks them complete only after actually doing that work, the
same honesty Phase 53's onboarding tracker already established.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_autonomous_agency.exceptions import CycleNotCompleteError
from careeros_common import DocumentStore

_ENTITY_TYPE = "agency_cycle_progress"


class AgencyStage(StrEnum):
    EMPLOYMENT = "employment"
    FREELANCE = "freelance"
    PERSONAL_BRAND = "personal_brand"
    NETWORKING = "networking"
    CLIENT_SUCCESS = "client_success"
    FINANCIAL_INTELLIGENCE = "financial_intelligence"
    CAREER_INTELLIGENCE = "career_intelligence"
    CEO_ALLOCATION = "ceo_allocation"
    LEARNING = "learning"


_STAGE_ORDER = list(AgencyStage)


class AgencyCycleProgress(BaseModel):
    subject_id: str
    completed_stages: list[AgencyStage] = Field(default_factory=list)
    cycles_completed: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def current_stage(self) -> AgencyStage | None:
        """The furthest stage reached, or None if nothing's been done yet."""
        completed_set = set(self.completed_stages)
        current = None
        for stage in _STAGE_ORDER:
            if stage in completed_set:
                current = stage
        return current

    @property
    def next_stage(self) -> AgencyStage | None:
        current = self.current_stage
        if current is None:
            return _STAGE_ORDER[0]
        index = _STAGE_ORDER.index(current)
        if index + 1 >= len(_STAGE_ORDER):
            return None
        return _STAGE_ORDER[index + 1]

    @property
    def is_cycle_complete(self) -> bool:
        return self.next_stage is None and self.current_stage is not None


class AgencyCycleProgressRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def load(self, subject_id: str) -> AgencyCycleProgress:
        data = self._store.get_or_none(_ENTITY_TYPE, subject_id)
        if data is None:
            return AgencyCycleProgress(subject_id=subject_id)
        return AgencyCycleProgress.model_validate(data)

    def mark_complete(self, subject_id: str, stage: AgencyStage) -> AgencyCycleProgress:
        progress = self.load(subject_id)
        if stage not in progress.completed_stages:
            progress.completed_stages.append(stage)
        progress.updated_at = datetime.now(UTC)
        self._store.put(_ENTITY_TYPE, subject_id, progress.model_dump(mode="json"))
        return progress

    def start_new_cycle(self, subject_id: str) -> AgencyCycleProgress:
        """CareerOS 'operates continuously': once every stage in a lap has
        been reached, loop back to the start for another — Better
        Decisions feeding Higher Lifetime Value isn't a discrete stage,
        it's what a completed lap earns before the next one begins.
        """
        progress = self.load(subject_id)
        if not progress.is_cycle_complete:
            raise CycleNotCompleteError(
                f"Subject {subject_id!r} has not completed every stage yet "
                f"(next stage: {progress.next_stage})"
            )
        progress.completed_stages = []
        progress.cycles_completed += 1
        progress.updated_at = datetime.now(UTC)
        self._store.put(_ENTITY_TYPE, subject_id, progress.model_dump(mode="json"))
        return progress
