"""A small, generic retry helper for flaky browser interactions."""

from __future__ import annotations

import time
from collections.abc import Callable

from careeros_common import get_logger

logger = get_logger(__name__)


def retry[T](
    fn: Callable[[], T],
    *,
    max_attempts: int = 3,
    backoff_seconds: float = 0.0,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call ``fn`` up to ``max_attempts`` times, re-raising the last error."""
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as exc:
            last_error = exc
            logger.warning("Attempt %d/%d failed: %s", attempt, max_attempts, exc)
            if attempt < max_attempts:
                sleep(backoff_seconds)
    assert last_error is not None
    raise last_error
