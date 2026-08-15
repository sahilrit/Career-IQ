"""Tests for Scheduler, entirely via injected timestamps — no real sleeps."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from careeros_runtime import Scheduler

T0 = datetime(2026, 1, 1, tzinfo=UTC)


def test_job_registered_with_start_at_now_is_due_on_first_tick():
    scheduler = Scheduler()
    scheduler.register("heartbeat", interval_seconds=60, fn=lambda: None, start_at=T0)
    due = scheduler.tick(T0)
    assert [job.name for job in due] == ["heartbeat"]


def test_job_is_not_due_before_its_interval_elapses():
    scheduler = Scheduler()
    scheduler.register("heartbeat", interval_seconds=60, fn=lambda: None, start_at=T0)
    scheduler.tick(T0)  # first run, reschedules to T0 + 60s
    due = scheduler.tick(T0 + timedelta(seconds=30))
    assert due == []


def test_job_is_due_again_after_its_interval_elapses():
    scheduler = Scheduler()
    scheduler.register("heartbeat", interval_seconds=60, fn=lambda: None, start_at=T0)
    scheduler.tick(T0)
    due = scheduler.tick(T0 + timedelta(seconds=60))
    assert [job.name for job in due] == ["heartbeat"]


def test_a_late_tick_reschedules_from_now_not_from_stale_due_time():
    scheduler = Scheduler()
    scheduler.register("heartbeat", interval_seconds=60, fn=lambda: None, start_at=T0)
    late = T0 + timedelta(seconds=500)  # ticker was delayed for a long time
    scheduler.tick(late)
    job = scheduler.jobs()[0]
    assert job.next_due_at == late + timedelta(seconds=60)


def test_unregister_removes_the_job():
    scheduler = Scheduler()
    scheduler.register("heartbeat", interval_seconds=60, fn=lambda: None, start_at=T0)
    scheduler.unregister("heartbeat")
    assert scheduler.jobs() == []
    assert scheduler.tick(T0) == []


def test_multiple_jobs_are_independent():
    scheduler = Scheduler()
    scheduler.register("fast", interval_seconds=10, fn=lambda: None, start_at=T0)
    scheduler.register("slow", interval_seconds=100, fn=lambda: None, start_at=T0)
    scheduler.tick(T0)  # both fire once

    due = scheduler.tick(T0 + timedelta(seconds=10))
    assert [job.name for job in due] == ["fast"]


def test_registering_the_same_name_twice_replaces_the_job():
    scheduler = Scheduler()
    calls = []
    scheduler.register("job", interval_seconds=60, fn=lambda: calls.append("first"), start_at=T0)
    scheduler.register("job", interval_seconds=60, fn=lambda: calls.append("second"), start_at=T0)

    due = scheduler.tick(T0)
    assert len(due) == 1
    due[0].fn()
    assert calls == ["second"]
