"""Worker: pulls callables off a queue and executes them on a background thread."""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable
from typing import Final

from careeros_common import get_logger

logger = get_logger(__name__)

SHUTDOWN: Final = object()  # sentinel telling a worker's loop to stop

QueueItem = Callable[[], None] | object


class Worker:
    def __init__(self, name: str, task_queue: queue.Queue[QueueItem]) -> None:
        self.name = name
        self._queue = task_queue
        self._thread: threading.Thread | None = None
        self.tasks_run = 0
        self.tasks_failed = 0

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name=self.name, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while True:
            item = self._queue.get()
            try:
                if item is SHUTDOWN:
                    return
                item()  # type: ignore[operator]
                self.tasks_run += 1
            except Exception:
                self.tasks_failed += 1
                logger.exception("Worker %s: task failed", self.name)
            finally:
                self._queue.task_done()

    def join(self, timeout: float | None = None) -> None:
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    @property
    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
