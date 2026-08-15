"""careeros_browser: browser automation abstraction for websites that
don't expose a useful free API. Playwright-backed, free and
open-source — no paid browser-automation service required.
"""

from careeros_browser.exceptions import BrowserError, DownloadError, SelectorTimeoutError
from careeros_browser.fake_session import FakeBrowserSession
from careeros_browser.health import check_browser_health
from careeros_browser.launcher import launch_browser_session
from careeros_browser.models import BrowserHealth, BrowserHealthStatus
from careeros_browser.playwright_session import PlaywrightBrowserSession
from careeros_browser.session import BrowserSession

__all__ = [
    "BrowserError",
    "BrowserHealth",
    "BrowserHealthStatus",
    "BrowserSession",
    "DownloadError",
    "FakeBrowserSession",
    "PlaywrightBrowserSession",
    "SelectorTimeoutError",
    "check_browser_health",
    "launch_browser_session",
]
