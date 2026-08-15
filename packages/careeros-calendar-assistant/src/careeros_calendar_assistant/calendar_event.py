"""CalendarEvent: a scheduled interview, built from extracted details."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from careeros_calendar_assistant.extraction import InterviewDetails
from careeros_calendar_assistant.stage import InterviewStage
from careeros_common import DocumentStore

_ENTITY_TYPE = "calendar_event"


class CalendarEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    application_id: str | None = None
    scheduled_at: datetime | None = None
    timezone: str | None = None
    platform: str | None = None
    meeting_link: str | None = None
    interviewers: list[str] = Field(default_factory=list)
    stage: InterviewStage = InterviewStage.UNKNOWN


def build_calendar_event(
    title: str, details: InterviewDetails, *, application_id: str | None = None
) -> CalendarEvent:
    return CalendarEvent(
        title=title,
        application_id=application_id,
        scheduled_at=details.scheduled_at,
        timezone=details.timezone,
        platform=details.platform,
        meeting_link=details.meeting_link,
        interviewers=details.interviewers,
        stage=details.stage,
    )


class CalendarEventRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, event: CalendarEvent) -> None:
        self._store.put(_ENTITY_TYPE, event.id, event.model_dump(mode="json"))

    def load(self, event_id: str) -> CalendarEvent:
        return CalendarEvent.model_validate(self._store.get(_ENTITY_TYPE, event_id))

    def load_or_none(self, event_id: str) -> CalendarEvent | None:
        data = self._store.get_or_none(_ENTITY_TYPE, event_id)
        return CalendarEvent.model_validate(data) if data else None

    def for_application(self, application_id: str) -> list[CalendarEvent]:
        return [
            CalendarEvent.model_validate(data)
            for data in self._store.list(_ENTITY_TYPE)
            if data.get("application_id") == application_id
        ]

    def list_all(self) -> list[CalendarEvent]:
        return [CalendarEvent.model_validate(data) for data in self._store.list(_ENTITY_TYPE)]
