"""Tests for WorkerPool + Worker: real background threads, deterministic
completion via wait_idle()/queue.join() rather than sleep-based polling.
"""

from __future__ import annotations

import threading

from careeros_runtime import WorkerPool


def test_submitted_task_runs_on_a_worker_thread():
    pool = WorkerPool(size=2)
    pool.start()
    try:
        done = threading.Event()
        pool.submit(done.set)
        assert done.wait(timeout=2)
        pool.wait_idle()
        assert pool.tasks_run() == 1
    finally:
        pool.stop()


def test_multiple_tasks_are_all_processed():
    pool = WorkerPool(size=3)
    pool.start()
    try:
        results: list[int] = []
        lock = threading.Lock()

        def make_task(i: int):
            def task() -> None:
                with lock:
                    results.append(i)

            return task

        for i in range(20):
            pool.submit(make_task(i))
        pool.wait_idle()

        assert sorted(results) == list(range(20))
        assert pool.tasks_run() == 20
    finally:
        pool.stop()


def test_a_failing_task_is_counted_and_does_not_kill_the_worker():
    pool = WorkerPool(size=1)
    pool.start()
    try:

        def broken() -> None:
            raise RuntimeError("boom")

        pool.submit(broken)
        pool.wait_idle()
        assert pool.tasks_failed() == 1

        done = threading.Event()
        pool.submit(done.set)
        assert done.wait(timeout=2)
        assert pool.tasks_run() == 1
    finally:
        pool.stop()


def test_stop_shuts_down_every_worker():
    pool = WorkerPool(size=3)
    pool.start()
    assert pool.alive_count() == 3
    pool.stop()
    assert pool.alive_count() == 0


def test_stop_is_idempotent():
    pool = WorkerPool(size=1)
    pool.start()
    pool.stop()
    pool.stop()  # must not raise
    assert pool.alive_count() == 0


def test_size_reports_configured_worker_count():
    pool = WorkerPool(size=5)
    assert pool.size == 5
