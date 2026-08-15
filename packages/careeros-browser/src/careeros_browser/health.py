"""Browser health check: can we actually launch a real browser right now?

``session_factory`` defaults to the real launcher but is injectable so
this can be tested against a fake context manager instead of launching
Chromium (see tests/test_health.py).
"""

from __future__ import annotations

from careeros_browser.launcher import launch_browser_session
from careeros_browser.models import BrowserHealth, BrowserHealthStatus


def check_browser_health(session_factory=launch_browser_session) -> BrowserHealth:
    try:
        with session_factory() as session:
            session.goto("about:blank")
    except Exception as exc:
        return BrowserHealth(status=BrowserHealthStatus.DOWN, detail=str(exc))
    return BrowserHealth(status=BrowserHealthStatus.HEALTHY)
