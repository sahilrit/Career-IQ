"""Event: the basic unit of communication on the Event Bus."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class Event(BaseModel):
    """A fact that happened, published for zero or more subscribers to react to.

    ``event_type`` is a dotted namespace, e.g. ``"job.discovered"`` or
    ``"application.status_changed"``. A publisher never knows who (if
    anyone) is subscribed — that indirection is the entire point of the
    bus: plugins and agents react to events instead of calling each other
    directly.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    source: str | None = None
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
