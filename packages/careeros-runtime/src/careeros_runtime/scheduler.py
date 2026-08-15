"""Scheduler: recurring job definitions and due-job selection.

Pure and clock-injectable: ``tick()`` takes the current time and returns
which registered jobs are due, rescheduling them from that same instant.
A production ``Runtime`` drives this from a background thread that calls
``tick()`` roughly once per interval (real wall-clock); tests call
``tick()`` directly with controlled timestamps, so scheduling logic is
fully deterministic without real sleeps.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class RecurringJob:
    name: str
    interval_seconds: float
    fn: Callable[[], None]
    next_due_at: datetime


class Scheduler:
    def __init__(self) -> None:
        self._jobs: dict[str, RecurringJob] = {}

    def register(
        self,
        name: str,
        interval_seconds: float,
        fn: Callable[[], None],
        *,
        start_at: datetime,
    ) -> None:
        self._jobs[name] = RecurringJob(
            name=name, interval_seconds=interval_seconds, fn=fn, next_due_at=start_at
        )

    def unregister(self, name: str) -> None:
        self._jobs.pop(name, None)

    def jobs(self) -> list[RecurringJob]:
        return list(self._jobs.values())

    def tick(self, now: datetime) -> list[RecurringJob]:
        """Return jobs due at/before ``now``, rescheduling each forward from ``now``.

        Rescheduling from ``now`` (rather than the stale ``next_due_at``)
        means a delayed tick can't cause a burst of immediately-due jobs
        on the following tick.
        """
        due = []
        for job in self._jobs.values():
            if job.next_due_at <= now:
                due.append(job)
                job.next_due_at = now + timedelta(seconds=job.interval_seconds)
        return due
