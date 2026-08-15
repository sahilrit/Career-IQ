"""Production safeguards: rate limits and per-company cooldowns.

These exist so an autonomous system (Phase 21+) can't flood a single
company with duplicate applications or blow past a sane daily volume —
independent of whether an opportunity scores well.
"""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from careeros_career_brain import ApplicationStatus, CareerBrain

_ONE_DAY_SECONDS = 86_400


class DailyApplicationLimiter:
    """Caps how many applications one identity can submit per rolling day."""

    def __init__(self, max_per_day: int, *, clock: Callable[[], float] = time.monotonic) -> None:
        self._max_per_day = max_per_day
        self._clock = clock
        self._submissions: dict[str, list[float]] = defaultdict(list)

    def record_submission(self, identity_id: str) -> None:
        self._submissions[identity_id].append(self._clock())

    def has_capacity(self, identity_id: str) -> bool:
        self._evict_expired(identity_id)
        return len(self._submissions[identity_id]) < self._max_per_day

    def _evict_expired(self, identity_id: str) -> None:
        cutoff = self._clock() - _ONE_DAY_SECONDS
        self._submissions[identity_id] = [
            timestamp for timestamp in self._submissions[identity_id] if timestamp >= cutoff
        ]


class CompanyCooldown:
    """Blocks reapplying to the same company within a cooldown window."""

    def __init__(self, cooldown_days: int = 90) -> None:
        self._cooldown = timedelta(days=cooldown_days)

    def is_on_cooldown(
        self, brain: CareerBrain, company_name: str, *, as_of: datetime | None = None
    ) -> bool:
        as_of = as_of or datetime.now(UTC)
        for application in brain.applications:
            if application.company_name != company_name:
                continue
            if application.status == ApplicationStatus.DISCOVERED:
                continue  # never actually applied, doesn't count against the cooldown
            applied_at = next(
                (
                    change.changed_at
                    for change in application.history
                    if change.status == ApplicationStatus.APPLIED
                ),
                None,
            )
            if applied_at is not None and as_of - applied_at < self._cooldown:
                return True
        return False
