"""Wraps a browser action with problem detection, handing off to a human
instead of failing outright or trying to defeat an obstacle
programmatically.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from careeros_browser import BrowserSession
from careeros_human_in_the_loop.detectors import Problem, ProblemDetector, run_detectors
from careeros_human_in_the_loop.handoff import HandoffSession, HandoffState


@dataclass
class ExecutionResult[T]:
    completed: bool
    value: T | None = None
    needs_human: bool = False


def run_with_human_fallback[T](
    session: BrowserSession,
    action: Callable[[], T],
    detectors: list[ProblemDetector],
    handoff: HandoffSession,
    *,
    screenshot_path: str | Path | None = None,
) -> ExecutionResult[T]:
    """Run ``action`` once.

    If a detector flags a problem before ``action`` even runs, or
    ``action`` itself raises, request a handoff instead of crashing. The
    caller resumes by calling ``resume()`` after a human calls
    ``handoff.resolve()``.
    """
    problem = run_detectors(session, detectors)
    if problem is None:
        try:
            value = action()
        except Exception as exc:
            problem = Problem(kind="execution_error", description=str(exc))
        else:
            return ExecutionResult(completed=True, value=value)

    screenshot = session.screenshot(screenshot_path) if screenshot_path else None
    handoff.request_takeover(problem, screenshot=screenshot)
    return ExecutionResult(completed=False, needs_human=True)


def resume[T](
    session: BrowserSession,
    action: Callable[[], T],
    detectors: list[ProblemDetector],
    handoff: HandoffSession,
    **kwargs: object,
) -> ExecutionResult[T]:
    """Re-attempt ``action`` after a human has resolved the handoff."""
    if handoff.state != HandoffState.RUNNING:
        raise ValueError("Cannot resume: handoff is not RUNNING (call handoff.resolve() first)")
    return run_with_human_fallback(session, action, detectors, handoff, **kwargs)
