"""Tests for Runtime: lifecycle, task submission, recurring jobs, health."""

from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta

from careeros_runtime import Runtime


def test_submit_task_runs_it_on_the_worker_pool():
    runtime = Runtime(worker_pool_size=2)
    runtime.start()
    try:
        done = threading.Event()
        runtime.submit_task(done.set)
        assert done.wait(timeout=2)
    finally:
        runtime.stop()


def test_run_due_jobs_enqueues_and_executes_a_freshly_registered_job():
    runtime = Runtime(worker_pool_size=1)
    runtime.start()
    try:
        done = threading.Event()
        runtime.register_recurring("heartbeat", interval_seconds=60, fn=done.set)
        enqueued = runtime.run_due_jobs()
        assert enqueued == 1
        assert done.wait(timeout=2)
    finally:
        runtime.stop()


def test_run_due_jobs_with_explicit_now_is_fully_deterministic():
    runtime = Runtime(worker_pool_size=1)
    runtime.start()
    try:
        calls: list[str] = []
        start = datetime(2026, 1, 1, tzinfo=UTC)
        runtime.register_recurring(
            "job", interval_seconds=60, fn=lambda: calls.append("ran"), start_at=start
        )

        assert runtime.run_due_jobs(now=start) == 1
        assert runtime.run_due_jobs(now=start + timedelta(seconds=30)) == 0
        assert runtime.run_due_jobs(now=start + timedelta(seconds=60)) == 1

        runtime.wait_idle()
        assert calls == ["ran", "ran"]
    finally:
        runtime.stop()


def test_unregister_recurring_stops_future_runs():
    runtime = Runtime(worker_pool_size=1)
    runtime.start()
    try:
        start = datetime(2026, 1, 1, tzinfo=UTC)
        runtime.register_recurring("job", interval_seconds=60, fn=lambda: None, start_at=start)
        runtime.unregister_recurring("job")

        assert runtime.run_due_jobs(now=start) == 0
    finally:
        runtime.stop()


def test_health_reports_running_state_and_registered_jobs():
    runtime = Runtime(worker_pool_size=3)
    assert runtime.health().running is False

    runtime.start()
    try:
        runtime.register_recurring("heartbeat", interval_seconds=60, fn=lambda: None)
        health = runtime.health()
        assert health.running is True
        assert health.worker_pool_size == 3
        assert health.alive_workers == 3
        assert health.registered_jobs == ["heartbeat"]
    finally:
        runtime.stop()

    assert runtime.health().running is False


def test_start_is_idempotent():
    runtime = Runtime(worker_pool_size=1)
    runtime.start()
    try:
        runtime.start()  # must not raise or double-start workers
        assert runtime.health().alive_workers == 1
    finally:
        runtime.stop()


def test_background_ticker_runs_recurring_jobs_without_manual_ticking():
    runtime = Runtime(worker_pool_size=1, tick_interval_seconds=0.05)
    done = threading.Event()
    runtime.register_recurring("heartbeat", interval_seconds=0.01, fn=done.set)
    runtime.start()
    try:
        assert done.wait(timeout=2)
    finally:
        runtime.stop()
