"""Append-only history logs derived from authoritative records and events.

Career Brain (``careeros_career_brain``) stays the single authoritative
source for *current* state. ``HistoryLog`` exists to answer "what
happened, and when" — application status changes, company research
notes, recruiter interactions, interview outcomes — without Career
Brain's current-state models needing to grow an ever-larger audit trail
inside themselves.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "history_entry"


class HistoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str
    subject_id: str
    summary: str
    details: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HistoryLog:
    """Append-only, queryable-by-category-and-subject history, on ``DocumentStore``."""

    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def append(self, entry: HistoryEntry) -> None:
        self._store.put(_ENTITY_TYPE, entry.id, entry.model_dump(mode="json"))

    def for_subject(self, category: str, subject_id: str) -> list[HistoryEntry]:
        matches = [e for e in self.all() if e.category == category and e.subject_id == subject_id]
        return matches

    def by_category(self, category: str) -> list[HistoryEntry]:
        return [e for e in self.all() if e.category == category]

    def all(self) -> list[HistoryEntry]:
        entries = [HistoryEntry.model_validate(d) for d in self._store.list(_ENTITY_TYPE)]
        return sorted(entries, key=lambda e: e.occurred_at)
