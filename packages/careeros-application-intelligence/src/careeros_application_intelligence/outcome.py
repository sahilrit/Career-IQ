"""Outcome tracking: recording what ultimately happened to an application.

Every outcome is written through Career Brain's own state machine
(``Application.transition_to``, so invalid transitions are still
rejected) and published on the event bus with the ``outcome.`` prefix
Memory's HistoryLog already subscribes to (Phase 5) — no direct
dependency between this package and Memory.
"""

from __future__ import annotations

from careeros_career_brain import (
    Application,
    ApplicationStatus,
    CareerBrain,
    CareerBrainRepository,
)
from careeros_event_bus import Event, EventBus


def record_outcome(
    repository: CareerBrainRepository,
    event_bus: EventBus,
    brain: CareerBrain,
    application: Application,
    new_status: ApplicationStatus,
    *,
    reason: str = "",
) -> None:
    application.transition_to(new_status, note=reason)
    repository.save(brain)
    event_bus.publish(
        Event(
            event_type="outcome.recorded",
            source="application-intelligence",
            payload={
                "subject_id": application.id,
                "company_name": application.company_name,
                "final_status": new_status.value,
                "reason": reason,
            },
        )
    )
