"""In-process, synchronous publish/subscribe event bus.

Plugins and agents publish events and subscribe to event-type patterns
instead of calling each other directly, so a new subscriber can be added
(or an existing one removed) without the publisher ever changing.
"""

from __future__ import annotations

import fnmatch
from collections import defaultdict
from collections.abc import Callable

from careeros_common import get_logger
from careeros_event_bus.event import Event

logger = get_logger(__name__)

EventHandler = Callable[[Event], None]


class EventBus:
    """Publish/subscribe dispatch keyed by fnmatch-style event-type patterns.

    A subscription to ``"job.*"`` matches ``"job.discovered"`` and
    ``"job.scored"``; ``"*"`` matches everything. Dispatch here is
    synchronous and in-process — Phase 9's runtime adds queued/async
    delivery on top without changing this publish/subscribe contract.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._history: list[Event] = []

    def subscribe(self, pattern: str, handler: EventHandler) -> None:
        self._subscribers[pattern].append(handler)

    def unsubscribe(self, pattern: str, handler: EventHandler) -> None:
        handlers = self._subscribers.get(pattern, [])
        if handler in handlers:
            handlers.remove(handler)

    def publish(self, event: Event) -> None:
        """Dispatch ``event`` to every matching subscriber.

        A handler that raises is logged and skipped — one broken
        subscriber must never stop the event from reaching the others or
        crash the publisher.
        """
        self._history.append(event)
        for pattern, handlers in self._subscribers.items():
            if not fnmatch.fnmatchcase(event.event_type, pattern):
                continue
            for handler in list(handlers):
                try:
                    handler(event)
                except Exception:
                    logger.exception(
                        "Event handler %r failed for event %s (%s)",
                        handler,
                        event.event_type,
                        event.id,
                    )

    def history(self, event_type: str | None = None) -> list[Event]:
        """Every event published so far, optionally filtered by pattern."""
        if event_type is None:
            return list(self._history)
        return [e for e in self._history if fnmatch.fnmatchcase(e.event_type, event_type)]
