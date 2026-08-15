"""WorkerPool: N Worker threads sharing one task queue."""

from __future__ import annotations

import queue
from collections.abc import Callable

from careeros_runtime.worker import SHUTDOWN, QueueItem, Worker


class WorkerPool:
    def __init__(self, size: int = 4) -> None:
        self._queue: queue.Queue[QueueItem] = queue.Queue()
        self._workers = [Worker(f"worker-{i}", self._queue) for i in range(size)]
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        for worker in self._workers:
            worker.start()
        self._started = True

    def submit(self, task: Callable[[], None]) -> None:
        self._queue.put(task)

    def wait_idle(self) -> None:
        """Block until every task submitted so far has finished running."""
        self._queue.join()

    def stop(self) -> None:
        if not self._started:
            return
        for _ in self._workers:
            self._queue.put(SHUTDOWN)
        for worker in self._workers:
            worker.join(timeout=5)
        self._started = False

    @property
    def size(self) -> int:
        return len(self._workers)

    def alive_count(self) -> int:
        return sum(1 for worker in self._workers if worker.is_alive)

    def tasks_run(self) -> int:
        return sum(worker.tasks_run for worker in self._workers)

    def tasks_failed(self) -> int:
        return sum(worker.tasks_failed for worker in self._workers)
