"""Tests for RateLimiter."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from careeros_trust_layer import RateLimiter


class _FakeClock:
    def __init__(self, start: datetime) -> None:
        self._now = start

    def __call__(self) -> datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)


def test_allows_up_to_max_actions():
    clock = _FakeClock(datetime(2026, 1, 1, tzinfo=UTC))
    limiter = RateLimiter(max_actions=3, window_seconds=60, clock=clock)
    assert limiter.try_acquire("user-1") is True
    assert limiter.try_acquire("user-1") is True
    assert limiter.try_acquire("user-1") is True
    assert limiter.try_acquire("user-1") is False


def test_window_resets_after_expiry():
    clock = _FakeClock(datetime(2026, 1, 1, tzinfo=UTC))
    limiter = RateLimiter(max_actions=1, window_seconds=60, clock=clock)
    assert limiter.try_acquire("user-1") is True
    assert limiter.try_acquire("user-1") is False
    clock.advance(61)
    assert limiter.try_acquire("user-1") is True


def test_limits_are_isolated_per_actor():
    clock = _FakeClock(datetime(2026, 1, 1, tzinfo=UTC))
    limiter = RateLimiter(max_actions=1, window_seconds=60, clock=clock)
    assert limiter.try_acquire("user-1") is True
    assert limiter.try_acquire("user-2") is True


def test_allow_does_not_record():
    clock = _FakeClock(datetime(2026, 1, 1, tzinfo=UTC))
    limiter = RateLimiter(max_actions=1, window_seconds=60, clock=clock)
    assert limiter.allow("user-1") is True
    assert limiter.allow("user-1") is True
