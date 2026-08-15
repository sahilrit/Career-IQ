"""EventContractRegistry: optional payload-shape validation for the Event Bus.

Phase 4's EventBus is deliberately unopinionated about payload shape —
that keeps it simple and general. This adds an *optional* layer on top:
register a pydantic model as the expected payload shape for an
event_type, and validate against it before publishing, without changing
EventBus itself. Event types with no registered contract behave exactly
as before.
"""

from __future__ import annotations

from pydantic import BaseModel, ValidationError

from careeros_core.exceptions import ContractViolationError
from careeros_event_bus import Event, EventBus


class EventContractRegistry:
    def __init__(self) -> None:
        self._contracts: dict[str, type[BaseModel]] = {}

    def register(self, event_type: str, schema: type[BaseModel]) -> None:
        self._contracts[event_type] = schema

    def validate(self, event: Event) -> None:
        schema = self._contracts.get(event.event_type)
        if schema is None:
            return
        try:
            schema.model_validate(event.payload)
        except ValidationError as exc:
            raise ContractViolationError(
                f"Event {event.event_type!r} payload does not match its registered contract: {exc}"
            ) from exc

    def publish(self, bus: EventBus, event: Event) -> None:
        """Validate then publish — the only way this registry touches the bus."""
        self.validate(event)
        bus.publish(event)
