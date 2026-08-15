"""HandoffSession: the state machine coordinating AI execution and human takeover.

    AI executes -> Problem detected -> Human takeover -> Human resolves -> AI resumes

Every transition is published on the event bus (``handoff.*``) so a
dashboard, chat bot, or CLI prompt can notify a human without this
module knowing anything about how that notification actually happens.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from careeros_event_bus import Event, EventBus
from careeros_human_in_the_loop.detectors import Problem


class HandoffState(StrEnum):
    RUNNING = "running"
    AWAITING_HUMAN = "awaiting_human"
    ABANDONED = "abandoned"


@dataclass
class HandoffRecord:
    problem: Problem
    screenshot: Path | None
    requested_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolution_note: str = ""
    resolved_at: datetime | None = None


class HandoffSession:
    """One task's AI/human handoff lifecycle."""

    def __init__(self, task_id: str, event_bus: EventBus) -> None:
        self.task_id = task_id
        self._bus = event_bus
        self.state = HandoffState.RUNNING
        self.records: list[HandoffRecord] = []

    def request_takeover(self, problem: Problem, *, screenshot: Path | None = None) -> None:
        self.state = HandoffState.AWAITING_HUMAN
        self.records.append(HandoffRecord(problem=problem, screenshot=screenshot))
        self._bus.publish(
            Event(
                event_type="handoff.requested",
                source="human-in-the-loop",
                payload={
                    "subject_id": self.task_id,
                    "kind": problem.kind,
                    "description": problem.description,
                    "screenshot": str(screenshot) if screenshot else None,
                },
            )
        )

    def resolve(self, *, note: str = "") -> None:
        if self.state != HandoffState.AWAITING_HUMAN:
            raise ValueError(f"Cannot resolve a handoff in state {self.state.value!r}")
        self.records[-1].resolution_note = note
        self.records[-1].resolved_at = datetime.now(UTC)
        self.state = HandoffState.RUNNING
        self._bus.publish(
            Event(
                event_type="handoff.resolved",
                source="human-in-the-loop",
                payload={"subject_id": self.task_id, "note": note},
            )
        )

    def abandon(self, *, reason: str = "") -> None:
        self.state = HandoffState.ABANDONED
        self._bus.publish(
            Event(
                event_type="handoff.abandoned",
                source="human-in-the-loop",
                payload={"subject_id": self.task_id, "reason": reason},
            )
        )

    @property
    def is_awaiting_human(self) -> bool:
        return self.state == HandoffState.AWAITING_HUMAN
