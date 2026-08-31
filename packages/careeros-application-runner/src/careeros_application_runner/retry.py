"""A small, generic retry helper for flaky browser interactions.

Retrying is for TRANSIENT failures — a slow render, a click that missed. Some
failures are facts about the form and will be exactly as true on the third
attempt as on the first: a required field the profile has no value for, a
control that is not the submit button. Retrying those costs the user two more
full form fills (which on a real ATS means re-uploading the résumé twice more)
and ends in the same place.

So a failure can declare itself terminal, and the loop stops immediately.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from careeros_common import get_logger

logger = get_logger(__name__)


class TerminalError(Exception):
    """A failure that repeating cannot fix. ``retry`` re-raises it at once."""


def retry[T](
    fn: Callable[[], T],
    *,
    max_attempts: int = 3,
    backoff_seconds: float = 0.0,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call ``fn`` up to ``max_attempts`` times, re-raising the last error.

    A ``TerminalError`` is re-raised on the first attempt: it is a statement
    about the form, not about the attempt.
    """
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except TerminalError as exc:
            logger.warning(
                "Attempt %d/%d failed terminally, not retrying: %s", attempt, max_attempts, exc
            )
            raise
        except Exception as exc:
            last_error = exc
            logger.warning("Attempt %d/%d failed: %s", attempt, max_attempts, exc)
            if attempt < max_attempts:
                sleep(backoff_seconds)
    assert last_error is not None
    raise last_error
