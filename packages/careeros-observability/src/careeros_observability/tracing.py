"""Tracer: a minimal, real span tracer — no OpenTelemetry dependency,
just enough to answer "what happened, in what order, and how long did
each step take" for one execution. Clock-injectable, the same testing
pattern as WorkingMemory/Scheduler/PacingLimiter.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from pydantic import BaseModel, Field


class Span(BaseModel):
    span_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    parent_span_id: str | None = None
    started_at: datetime
    ended_at: datetime | None = None
    attributes: dict[str, str] = Field(default_factory=dict)

    @property
    def duration_seconds(self) -> float | None:
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()


class Tracer:
    def __init__(self, *, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(UTC))
        self._spans: list[Span] = []
        self._active_span_stack: list[str] = []

    @contextmanager
    def span(self, name: str, **attributes: str) -> Iterator[Span]:
        parent_id = self._active_span_stack[-1] if self._active_span_stack else None
        current_span = Span(
            name=name, parent_span_id=parent_id, started_at=self._clock(), attributes=attributes
        )
        self._spans.append(current_span)
        self._active_span_stack.append(current_span.span_id)
        try:
            yield current_span
        finally:
            self._active_span_stack.pop()
            current_span.ended_at = self._clock()

    def spans(self) -> list[Span]:
        return list(self._spans)
