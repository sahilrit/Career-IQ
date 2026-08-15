"""Wires Event Bus events into HistoryLog entries.

Memory subscribes to events instead of Career Brain (or anything else)
calling into it directly — matching the Phase 4 principle that plugins
and agents communicate through the bus, not through direct references to
each other.
"""

from __future__ import annotations

from careeros_event_bus import Event, EventBus
from careeros_memory.history import HistoryEntry, HistoryLog

_CATEGORY_BY_EVENT_PREFIX: dict[str, str] = {
    "application.": "application",
    "company.": "company",
    "recruiter.": "recruiter",
    "interview.": "interview",
    "outcome.": "outcome",
}


def category_for_event(event_type: str) -> str | None:
    for prefix, category in _CATEGORY_BY_EVENT_PREFIX.items():
        if event_type.startswith(prefix):
            return category
    return None


def record_event_in_history(log: HistoryLog, event: Event) -> None:
    category = category_for_event(event.event_type)
    if category is None:
        return
    subject_id = event.payload.get("subject_id") or event.payload.get("id") or event.id
    log.append(
        HistoryEntry(
            category=category,
            subject_id=str(subject_id),
            summary=event.event_type,
            details=event.payload,
        )
    )


def attach_history_logging(bus: EventBus, log: HistoryLog) -> None:
    """Subscribe ``log`` to every history-relevant event published on ``bus``."""
    bus.subscribe("*", lambda event: record_event_in_history(log, event))
