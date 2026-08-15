"""Tests for PacingLimiter, using an injectable fake clock."""

from __future__ import annotations

from careeros_autonomy import PacingLimiter


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_ready_before_any_action():
    limiter = PacingLimiter(10.0, clock=_FakeClock())
    assert limiter.ready() is True


def test_not_ready_immediately_after_an_action():
    clock = _FakeClock()
    limiter = PacingLimiter(10.0, clock=clock)
    limiter.record_action()
    assert limiter.ready() is False


def test_ready_again_after_the_interval_elapses():
    clock = _FakeClock()
    limiter = PacingLimiter(10.0, clock=clock)
    limiter.record_action()
    clock.advance(10.0)
    assert limiter.ready() is True


def test_seconds_until_ready_counts_down():
    clock = _FakeClock()
    limiter = PacingLimiter(10.0, clock=clock)
    limiter.record_action()
    clock.advance(4.0)
    assert limiter.seconds_until_ready() == 6.0


def test_seconds_until_ready_never_negative():
    clock = _FakeClock()
    limiter = PacingLimiter(10.0, clock=clock)
    limiter.record_action()
    clock.advance(100.0)
    assert limiter.seconds_until_ready() == 0.0
