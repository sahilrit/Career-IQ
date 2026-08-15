"""Wires agency-cycle stage tracking to events already published by
earlier phases — application.autonomously_submitted (Phase 22),
client.won and company.qualified (Phase 31) — with no direct package
dependency on any of them, the same event-bus-over-import principle
Phase 4 established and Phase 30/33 already applied.

Only mapped where the semantics genuinely match: an autonomously
submitted application is real Employment-side progress; winning a
client is real Freelance-side progress; qualifying a company is a real
relationship forming, the same signal Phase 33's CRM uses for its own
Networking stage. Personal Brand, Client Success, Financial
Intelligence, Career Intelligence, CEO Allocation, and Learning have no
corresponding platform event yet — those divisions compute real work
directly rather than through the bus, so the caller marks those stages
complete after actually doing that work.
"""

from __future__ import annotations

from careeros_autonomous_agency.cycle_stage import AgencyCycleProgressRepository, AgencyStage
from careeros_event_bus import Event, EventBus

_EVENT_STAGE_MAP: dict[str, AgencyStage] = {
    "application.autonomously_submitted": AgencyStage.EMPLOYMENT,
    "client.won": AgencyStage.FREELANCE,
    "company.qualified": AgencyStage.NETWORKING,
}


def handle_event(progress_repository: AgencyCycleProgressRepository, event: Event) -> None:
    stage = _EVENT_STAGE_MAP.get(event.event_type)
    if stage is None:
        return
    subject_id = event.payload.get("subject_id")
    if subject_id:
        progress_repository.mark_complete(str(subject_id), stage)


def wire_agency_cycle(bus: EventBus, progress_repository: AgencyCycleProgressRepository) -> None:
    bus.subscribe("*", lambda event: handle_event(progress_repository, event))
