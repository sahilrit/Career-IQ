"""Runtime: the top-level lifecycle for turning functions into a
continuously running system.

Composes a ``WorkerPool`` (executes submitted tasks concurrently) with a
``Scheduler`` (decides which recurring jobs are due). A background
"ticker" thread drives the scheduler once per ``tick_interval_seconds``
in production; tests instead call ``run_due_jobs(now=...)`` directly for
deterministic, sleep-free control over recurring-job behavior.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import UTC, datetime

from careeros_common import get_logger
from careeros_runtime.health import RuntimeHealth
from careeros_runtime.pool import WorkerPool
from careeros_runtime.scheduler import Scheduler

logger = get_logger(__name__)


class Runtime:
    def __init__(self, *, worker_pool_size: int = 4, tick_interval_seconds: float = 1.0) -> None:
        self._pool = WorkerPool(worker_pool_size)
        self._scheduler = Scheduler()
        self._tick_interval = tick_interval_seconds
        self._ticker_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._pool.start()
        self._stop_event.clear()
        self._ticker_thread = threading.Thread(
            target=self._tick_loop, name="scheduler-ticker", daemon=True
        )
        self._ticker_thread.start()
        self._running = True
        logger.info("Runtime started with %d workers", self._pool.size)

    def stop(self) -> None:
        if not self._running:
            return
        self._stop_event.set()
        if self._ticker_thread is not None:
            self._ticker_thread.join(timeout=5)
        self._pool.stop()
        self._running = False
        logger.info("Runtime stopped")

    def submit_task(self, task: Callable[[], None]) -> None:
        self._pool.submit(task)

    def register_recurring(
        self,
        name: str,
        interval_seconds: float,
        fn: Callable[[], None],
        *,
        start_at: datetime | None = None,
    ) -> None:
        """Register a job due at ``start_at`` (default: now), then every ``interval_seconds``."""
        self._scheduler.register(name, interval_seconds, fn, start_at=start_at or datetime.now(UTC))

    def unregister_recurring(self, name: str) -> None:
        self._scheduler.unregister(name)

    def run_due_jobs(self, now: datetime | None = None) -> int:
        """Enqueue every job due at ``now`` (defaults to current time). Returns count enqueued."""
        due = self._scheduler.tick(now or datetime.now(UTC))
        for job in due:
            self._pool.submit(job.fn)
        return len(due)

    def _tick_loop(self) -> None:
        while not self._stop_event.is_set():
            self.run_due_jobs()
            self._stop_event.wait(self._tick_interval)

    def health(self) -> RuntimeHealth:
        return RuntimeHealth(
            running=self._running,
            worker_pool_size=self._pool.size,
            alive_workers=self._pool.alive_count(),
            tasks_run=self._pool.tasks_run(),
            tasks_failed=self._pool.tasks_failed(),
            registered_jobs=[job.name for job in self._scheduler.jobs()],
        )

    def wait_idle(self) -> None:
        self._pool.wait_idle()
