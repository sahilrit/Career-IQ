"""Wires the relationship timeline to events already published by
earlier phases — company.qualified / client.won (Phase 31),
outcome.recorded (Phase 16) — with no direct package dependency on any
of them, the same event-bus-over-import principle Phase 4 established.

Only mapped where the semantics genuinely match: qualifying a company
is a real business opportunity forming with that contact; winning a
client or accepting a job offer is the relationship reaching its final
stage. Earlier engagement stages (Viewed/Liked/Commented/Connected/
Messaged/Conversation) have no corresponding platform event yet — a
future LinkedIn engagement automation (Phase 34) would record those
directly via ``TimelineRepository.record()``, rather than this module
inventing semantics no event actually carries.
"""

from __future__ import annotations

from careeros_crm.timeline import RelationshipStage, TimelineRepository
from careeros_event_bus import Event, EventBus

_EVENT_STAGE_MAP: dict[str, RelationshipStage] = {
    "company.qualified": RelationshipStage.OPPORTUNITY,
    "client.won": RelationshipStage.CLIENT_OR_EMPLOYER,
}

_OUTCOME_STAGE_MAP: dict[str, RelationshipStage] = {
    "accepted": RelationshipStage.CLIENT_OR_EMPLOYER,
}


def handle_event(timeline_repository: TimelineRepository, event: Event) -> None:
    contact_id = event.payload.get("subject_id")
    if not contact_id:
        return

    if event.event_type == "outcome.recorded":
        stage = _OUTCOME_STAGE_MAP.get(event.payload.get("final_status", ""))
    else:
        stage = _EVENT_STAGE_MAP.get(event.event_type)

    if stage is not None:
        timeline_repository.record(contact_id, stage, detail=event.event_type)


def wire_crm(bus: EventBus, timeline_repository: TimelineRepository) -> None:
    bus.subscribe("*", lambda event: handle_event(timeline_repository, event))
