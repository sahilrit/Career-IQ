"""MeetingNote: a record of a client meeting and its action items —
always something the user actually wrote down, never generated.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "meeting_note"


class MeetingNote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    summary: str
    action_items: list[str] = Field(default_factory=list)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MeetingNoteRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, note: MeetingNote) -> None:
        self._store.put(_ENTITY_TYPE, note.id, note.model_dump(mode="json"))

    def list_for_client(self, client_id: str) -> list[MeetingNote]:
        return [
            MeetingNote.model_validate(data)
            for data in self._store.list(_ENTITY_TYPE)
            if data.get("client_id") == client_id
        ]
