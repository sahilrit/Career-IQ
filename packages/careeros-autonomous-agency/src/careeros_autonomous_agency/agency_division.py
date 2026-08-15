"""AutonomousAgencyDivision: the facade tying cycle-stage tracking and
real-event wiring together. This is the platform's final composition —
every stage it tracks is real work already done by an earlier phase's
own package; this division adds no new domain logic, only the
continuous-loop view across all of it.
"""

from __future__ import annotations

from careeros_autonomous_agency.cycle_stage import (
    AgencyCycleProgress,
    AgencyCycleProgressRepository,
    AgencyStage,
)
from careeros_autonomous_agency.events import wire_agency_cycle
from careeros_common import DocumentStore
from careeros_event_bus import EventBus


class AutonomousAgencyDivision:
    def __init__(self, store: DocumentStore, *, event_bus: EventBus | None = None) -> None:
        self._progress = AgencyCycleProgressRepository(store)
        if event_bus is not None:
            wire_agency_cycle(event_bus, self._progress)

    def progress_for(self, subject_id: str) -> AgencyCycleProgress:
        return self._progress.load(subject_id)

    def mark_complete(self, subject_id: str, stage: AgencyStage) -> AgencyCycleProgress:
        return self._progress.mark_complete(subject_id, stage)

    def start_new_cycle(self, subject_id: str) -> AgencyCycleProgress:
        return self._progress.start_new_cycle(subject_id)
