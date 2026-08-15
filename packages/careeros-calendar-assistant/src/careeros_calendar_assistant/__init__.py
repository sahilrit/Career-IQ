"""careeros_calendar_assistant: the personal operations layer. Turns an
interview email straight into a CalendarEvent and an EventWorkspace
bundling every related material, with no manual data entry.
"""

from careeros_calendar_assistant.calendar_event import (
    CalendarEvent,
    CalendarEventRepository,
    build_calendar_event,
)
from careeros_calendar_assistant.extraction import InterviewDetails, extract_interview_details
from careeros_calendar_assistant.stage import InterviewStage, detect_stage
from careeros_calendar_assistant.workflow import process_interview_email
from careeros_calendar_assistant.workspace import EventWorkspace, EventWorkspaceRepository

__all__ = [
    "CalendarEvent",
    "CalendarEventRepository",
    "EventWorkspace",
    "EventWorkspaceRepository",
    "InterviewDetails",
    "InterviewStage",
    "build_calendar_event",
    "detect_stage",
    "extract_interview_details",
    "process_interview_email",
]
