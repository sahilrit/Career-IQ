"""Wires Employment Division pipeline stage tracking to events already
published by earlier phases — application.created / job.scored (Phase
8), application.autonomously_submitted (Phase 22), outcome.recorded
(Phase 16) — with no direct package dependency on any of them. This is
the same event-bus-over-direct-import principle Phase 4 established.
"""

from __future__ import annotations

from careeros_employment_division.pipeline_stage import PipelineProgressRepository, PipelineStage
from careeros_event_bus import Event, EventBus

_EVENT_STAGE_MAP: dict[str, PipelineStage] = {
    "application.created": PipelineStage.DISCOVERY,
    "job.scored": PipelineStage.SCORING,
    "application.autonomously_submitted": PipelineStage.APPLICATION,
}

_OUTCOME_STAGE_MAP: dict[str, PipelineStage] = {
    "interviewing": PipelineStage.INTERVIEW,
    "offer": PipelineStage.OFFER,
    "accepted": PipelineStage.NEGOTIATION,
}


def handle_event(progress_repository: PipelineProgressRepository, event: Event) -> None:
    stage = _EVENT_STAGE_MAP.get(event.event_type)
    if stage is not None:
        subject_id = event.payload.get("subject_id")
        if subject_id:
            progress_repository.mark_complete(str(subject_id), stage)
        return

    if event.event_type == "outcome.recorded":
        final_status = event.payload.get("final_status")
        stage = _OUTCOME_STAGE_MAP.get(final_status)
        subject_id = event.payload.get("subject_id")
        if stage is not None and subject_id:
            progress_repository.mark_complete(str(subject_id), stage)


def wire_pipeline_progress(bus: EventBus, progress_repository: PipelineProgressRepository) -> None:
    bus.subscribe("*", lambda event: handle_event(progress_repository, event))
