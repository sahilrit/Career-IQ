"""General-purpose rate limiter: a sliding window per actor, usable for
any action type — distinct from Phase 22's DailyApplicationLimiter,
which is specific to job applications. Clock-injectable, the same
testing pattern as WorkingMemory/Scheduler/PacingLimiter, so tests
never depend on real wall-clock time.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta


class RateLimiter:
    def __init__(
        self,
        *,
        max_actions: int,
        window_seconds: float,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._max_actions = max_actions
        self._window = timedelta(seconds=window_seconds)
        self._clock = clock or (lambda: datetime.now(UTC))
        self._history: dict[str, list[datetime]] = {}

    def _recent_actions(self, actor_id: str) -> list[datetime]:
        cutoff = self._clock() - self._window
        recent = [when for when in self._history.get(actor_id, []) if when >= cutoff]
        self._history[actor_id] = recent
        return recent

    def allow(self, actor_id: str) -> bool:
        return len(self._recent_actions(actor_id)) < self._max_actions

    def record(self, actor_id: str) -> None:
        self._history.setdefault(actor_id, []).append(self._clock())

    def try_acquire(self, actor_id: str) -> bool:
        """Atomically checks and records — the usual way to call this."""
        if not self.allow(actor_id):
            return False
        self.record(actor_id)
        return True
