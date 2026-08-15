"""SignalInput: one piece of already-computed evidence from elsewhere
in the platform (career-brain-engine's skill matching, opportunity
prediction's demand score, the learning lab's winning variant, ...).

This package is deliberately a pure combinator — it doesn't compute new
signals itself, it combines signals the rest of the platform already
produced. ``source`` records exactly where a signal came from, so a
recommendation can always be traced back to real evidence rather than
becoming a black box.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "signal_input"


class RecommendationCategory(StrEnum):
    ROLE = "role"
    COMPANY = "company"
    INDUSTRY = "industry"
    CLIENT = "client"
    COUNTRY = "country"
    SALARY_RANGE = "salary_range"
    SKILL = "skill"
    PLATFORM = "platform"
    OUTREACH_STRATEGY = "outreach_strategy"
    RESUME_VARIANT = "resume_variant"


class SignalInput(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: RecommendationCategory
    subject: str
    score: float
    source: str
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SignalInputRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, signal: SignalInput) -> None:
        self._store.put(_ENTITY_TYPE, signal.id, signal.model_dump(mode="json"))

    def list_all(self) -> list[SignalInput]:
        return [SignalInput.model_validate(data) for data in self._store.list(_ENTITY_TYPE)]

    def list_by_category(self, category: RecommendationCategory) -> list[SignalInput]:
        return [signal for signal in self.list_all() if signal.category == category]
