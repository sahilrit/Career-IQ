"""MetricsRegistry: counters, gauges, and timers — in-process, no
external time-series database, so metrics work the same whether
CareerOS is self-hosted on a laptop or running as a production
service.
"""

from __future__ import annotations

from pydantic import BaseModel


class TimerStats(BaseModel):
    count: int
    total_seconds: float
    mean_seconds: float
    max_seconds: float


class MetricsSnapshot(BaseModel):
    counters: dict[str, float]
    gauges: dict[str, float]
    timers: dict[str, TimerStats]


class MetricsRegistry:
    def __init__(self) -> None:
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._timer_samples: dict[str, list[float]] = {}

    def increment_counter(self, name: str, value: float = 1.0) -> None:
        self._counters[name] = self._counters.get(name, 0.0) + value

    def set_gauge(self, name: str, value: float) -> None:
        self._gauges[name] = value

    def record_timer(self, name: str, duration_seconds: float) -> None:
        self._timer_samples.setdefault(name, []).append(duration_seconds)

    def snapshot(self) -> MetricsSnapshot:
        timers = {
            name: TimerStats(
                count=len(samples),
                total_seconds=sum(samples),
                mean_seconds=sum(samples) / len(samples),
                max_seconds=max(samples),
            )
            for name, samples in self._timer_samples.items()
        }
        return MetricsSnapshot(
            counters=dict(self._counters), gauges=dict(self._gauges), timers=timers
        )
