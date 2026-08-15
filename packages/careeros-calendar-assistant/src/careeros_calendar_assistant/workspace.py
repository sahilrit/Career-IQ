"""EventWorkspace: bundles the materials relevant to one interview — job
description, resume, cover letter, company research, interviewer info,
outreach thread, and interview notes — all in one place instead of
scattered across packages.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "event_workspace"


class EventWorkspace(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    calendar_event_id: str
    job_description: str = ""
    resume_text: str = ""
    cover_letter_text: str = ""
    company_research: str = ""
    interviewer_info: dict[str, str] = Field(default_factory=dict)
    outreach_thread: list[str] = Field(default_factory=list)
    interview_notes: str = ""


class EventWorkspaceRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, workspace: EventWorkspace) -> None:
        self._store.put(_ENTITY_TYPE, workspace.id, workspace.model_dump(mode="json"))

    def load(self, workspace_id: str) -> EventWorkspace:
        return EventWorkspace.model_validate(self._store.get(_ENTITY_TYPE, workspace_id))

    def load_or_none(self, workspace_id: str) -> EventWorkspace | None:
        data = self._store.get_or_none(_ENTITY_TYPE, workspace_id)
        return EventWorkspace.model_validate(data) if data else None

    def for_calendar_event(self, calendar_event_id: str) -> EventWorkspace | None:
        for data in self._store.list(_ENTITY_TYPE):
            if data.get("calendar_event_id") == calendar_event_id:
                return EventWorkspace.model_validate(data)
        return None
