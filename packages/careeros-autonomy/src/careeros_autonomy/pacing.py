"""PacingLimiter: a minimum interval between consecutive autonomous actions.

Not a daily application cap — the roadmap explicitly rejects an
arbitrary one ("it continues while qualified opportunities remain").
This exists purely to avoid hammering an external site with rapid-fire
requests, which is a real operational concern rather than an arbitrary
volume limit.
"""

from __future__ import annotations

import time
from collections.abc import Callable


class PacingLimiter:
    def __init__(
        self, min_seconds_between_actions: float, *, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._min_interval = min_seconds_between_actions
        self._clock = clock
        self._last_action_at: float | None = None

    def ready(self) -> bool:
        if self._last_action_at is None:
            return True
        return (self._clock() - self._last_action_at) >= self._min_interval

    def record_action(self) -> None:
        self._last_action_at = self._clock()

    def seconds_until_ready(self) -> float:
        if self._last_action_at is None:
            return 0.0
        remaining = self._min_interval - (self._clock() - self._last_action_at)
        return max(remaining, 0.0)
