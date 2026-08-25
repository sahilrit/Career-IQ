"""careeros_browser: browser automation abstraction for websites that
don't expose a useful free API. Playwright-backed, free and
open-source — no paid browser-automation service required.
"""

from careeros_browser.exceptions import (
    BrowserError,
    DownloadError,
    ResponseTimeoutError,
    SelectorTimeoutError,
)
from careeros_browser.fake_session import FakeBrowserSession
from careeros_browser.health import check_browser_health
from careeros_browser.launcher import launch_browser_session, launch_camoufox_session
from careeros_browser.matching import best_option_index
from careeros_browser.models import BrowserHealth, BrowserHealthStatus
from careeros_browser.playwright_session import PlaywrightBrowserSession
from careeros_browser.resilience import (
    CF_CHALLENGE_MARKERS,
    CookieJar,
    PersistentCookieStore,
    is_challenge_html,
    is_challenge_status,
    retry_with_backoff,
)
from careeros_browser.session import BrowserSession

__all__ = [
    "CF_CHALLENGE_MARKERS",
    "BrowserError",
    "BrowserHealth",
    "BrowserHealthStatus",
    "BrowserSession",
    "CookieJar",
    "DownloadError",
    "FakeBrowserSession",
    "PersistentCookieStore",
    "PlaywrightBrowserSession",
    "ResponseTimeoutError",
    "SelectorTimeoutError",
    "best_option_index",
    "check_browser_health",
    "is_challenge_html",
    "is_challenge_status",
    "launch_browser_session",
    "launch_camoufox_session",
    "retry_with_backoff",
]
