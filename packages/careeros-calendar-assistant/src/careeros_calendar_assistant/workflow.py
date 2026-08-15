"""The automatic interview workflow:

    Interview Email -> extracted details -> CalendarEvent -> EventWorkspace

ready for Phase 29's interview-prep materials to fill in.
"""

from __future__ import annotations

from careeros_calendar_assistant.calendar_event import (
    CalendarEvent,
    CalendarEventRepository,
    build_calendar_event,
)
from careeros_calendar_assistant.extraction import extract_interview_details
from careeros_calendar_assistant.workspace import EventWorkspace, EventWorkspaceRepository
from careeros_communication_intelligence import CommunicationCategory, EmailMessage, classify


def process_interview_email(
    message: EmailMessage,
    calendar_repo: CalendarEventRepository,
    workspace_repo: EventWorkspaceRepository,
    *,
    application_id: str | None = None,
) -> CalendarEvent | None:
    """Only proceeds if the message classifies as an interview email."""
    if classify(message.subject, message.body) != CommunicationCategory.INTERVIEW:
        return None

    details = extract_interview_details(message.subject, message.body)
    event = build_calendar_event(message.subject, details, application_id=application_id)
    calendar_repo.save(event)

    workspace = EventWorkspace(calendar_event_id=event.id)
    workspace_repo.save(workspace)

    return event
