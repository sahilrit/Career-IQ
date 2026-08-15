"""Problem detection: pluggable checks for "does the AI need a human right now?"

No captcha-solving, no bypass techniques — CareerOS's answer to a captcha
or an unexpected page state is always to hand off to a human, never to
defeat it programmatically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol

from careeros_browser import BrowserSession


@dataclass
class Problem:
    kind: str
    description: str
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class ProblemDetector(Protocol):
    def detect(self, session: BrowserSession) -> Problem | None: ...


class SelectorAppearsDetector:
    """Flags a problem when a selector that shouldn't be there shows up (e.g. a captcha)."""

    def __init__(
        self, selector: str, *, kind: str = "blocking_element", description: str | None = None
    ) -> None:
        self._selector = selector
        self._kind = kind
        self._description = description or f"Unexpected element appeared: {selector}"

    def detect(self, session: BrowserSession) -> Problem | None:
        if session.is_visible(self._selector):
            return Problem(kind=self._kind, description=self._description)
        return None


class SelectorMissingDetector:
    """Flags a problem when a selector that should be there is absent."""

    def __init__(
        self, selector: str, *, kind: str = "missing_element", description: str | None = None
    ) -> None:
        self._selector = selector
        self._kind = kind
        self._description = description or f"Expected element missing: {selector}"

    def detect(self, session: BrowserSession) -> Problem | None:
        if not session.is_visible(self._selector):
            return Problem(kind=self._kind, description=self._description)
        return None


def run_detectors(session: BrowserSession, detectors: list[ProblemDetector]) -> Problem | None:
    for detector in detectors:
        problem = detector.detect(session)
        if problem is not None:
            return problem
    return None
