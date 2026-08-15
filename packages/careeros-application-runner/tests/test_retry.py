"""Tests for the generic retry helper."""

from __future__ import annotations

import pytest

from careeros_application_runner import retry


def test_succeeds_on_first_attempt_without_retrying():
    calls = []

    def fn():
        calls.append(1)
        return "ok"

    result = retry(fn, max_attempts=3, sleep=lambda seconds: None)
    assert result == "ok"
    assert len(calls) == 1


def test_retries_until_success():
    attempts = {"count": 0}

    def fn():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("not yet")
        return "ok"

    result = retry(fn, max_attempts=5, sleep=lambda seconds: None)
    assert result == "ok"
    assert attempts["count"] == 3


def test_raises_the_last_error_after_exhausting_attempts():
    def fn():
        raise ValueError("always fails")

    with pytest.raises(ValueError, match="always fails"):
        retry(fn, max_attempts=3, sleep=lambda seconds: None)


def test_sleeps_between_attempts_with_the_configured_backoff():
    sleeps = []

    def fn():
        raise RuntimeError("fails")

    with pytest.raises(RuntimeError):
        retry(fn, max_attempts=3, backoff_seconds=2.5, sleep=sleeps.append)

    assert sleeps == [2.5, 2.5]  # called between attempts 1->2 and 2->3, not after the last


def test_does_not_sleep_after_the_final_attempt():
    sleeps = []
    attempts = {"count": 0}

    def fn():
        attempts["count"] += 1
        if attempts["count"] == 2:
            return "ok"
        raise RuntimeError("fails")

    retry(fn, max_attempts=2, backoff_seconds=1.0, sleep=sleeps.append)
    assert sleeps == [1.0]
