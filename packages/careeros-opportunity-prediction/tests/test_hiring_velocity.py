"""Tests for compute_hiring_velocity_signal."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from careeros_opportunity_prediction import SignalType, compute_hiring_velocity_signal

_NOW = datetime(2026, 6, 1, tzinfo=UTC)


def test_below_threshold_returns_none():
    dates = [_NOW - timedelta(days=10), _NOW - timedelta(days=20)]
    assert compute_hiring_velocity_signal("company-1", dates, now=_NOW) is None


def test_at_threshold_returns_a_signal():
    dates = [_NOW - timedelta(days=d) for d in (10, 20, 30)]
    signal = compute_hiring_velocity_signal("company-1", dates, now=_NOW)
    assert signal is not None
    assert signal.signal_type == SignalType.HIRING_VELOCITY
    assert "3 job postings" in signal.detail


def test_postings_outside_the_window_are_excluded():
    dates = [_NOW - timedelta(days=10), _NOW - timedelta(days=200), _NOW - timedelta(days=300)]
    assert compute_hiring_velocity_signal("company-1", dates, now=_NOW) is None


def test_custom_thresholds_are_respected():
    dates = [_NOW - timedelta(days=5), _NOW - timedelta(days=6)]
    signal = compute_hiring_velocity_signal("company-1", dates, now=_NOW, min_postings=2)
    assert signal is not None
