"""Launches real browser sessions.

Two launchers, same ``BrowserSession`` on the other end:

``launch_browser_session`` — vanilla Playwright Chromium. Requires the
``playwright`` package (already a dependency) and its browser binaries,
installed once, locally, for free via ``uv run playwright install
chromium`` — never a paid step and never required just to import this
module. Fine for sites with no bot defenses.

``launch_camoufox_session`` — Camoufox, an anti-detect Firefox build
(free, MPL-2.0) that spoofs device fingerprints, GeoIP, timezone and
locale so headless traffic reads as a real browser. Needed for sites
behind Cloudflare or similar (Naukri, Gradcracker). Requires the
``camoufox`` package plus its browser binary, fetched once via
``python3 -m camoufox fetch`` — likewise never required just to import
this module, and never a paid step.

Camoufox wraps Playwright's own context manager and hands back a real
Playwright ``Browser`` (confirmed from its source: ``Camoufox(**opts)``
is a ``PlaywrightContextManager`` subclass whose ``__enter__`` returns
the launched browser), so ``PlaywrightBrowserSession`` — built against
Playwright's ``Page`` interface — wraps a Camoufox page exactly as it
wraps a Chromium one. No separate session class needed.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from careeros_browser.exceptions import BrowserError
from careeros_browser.playwright_session import PlaywrightBrowserSession


@contextmanager
def launch_browser_session(*, headless: bool = True) -> Iterator[PlaywrightBrowserSession]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise BrowserError("playwright is not installed. Run `uv sync --all-packages`.") from exc

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        page = browser.new_page()
        session = PlaywrightBrowserSession(page)
        try:
            yield session
        finally:
            session.close()
            browser.close()


@contextmanager
def launch_camoufox_session(
    *,
    headless: bool = True,
    humanize: bool = True,
    geoip: bool = True,
    user_agent: str | None = None,
) -> Iterator[PlaywrightBrowserSession]:
    """Launch an anti-detect Camoufox session.

    ``user_agent`` should be the UA a previous challenge solve was captured
    under (see ``careeros_browser.resilience.CookieJar``) — the anti-bot
    layer ties a solved clearance cookie to the UA (and TLS fingerprint)
    that earned it, so replaying the cookie under a different UA is
    worthless. Omit it for a fresh session with no prior clearance.

    ``block_images`` is deliberately not exposed: Cloudflare's own docs
    note it checks whether images actually loaded, so blocking them is a
    detection signal in itself.
    """
    try:
        from camoufox.sync_api import Camoufox
    except ImportError as exc:
        raise BrowserError(
            "camoufox is not installed. Run `uv sync --all-packages` then "
            "`python3 -m camoufox fetch` to download the browser binary."
        ) from exc

    launch_options: dict[str, object] = {"headless": headless, "humanize": humanize, "geoip": geoip}
    if user_agent:
        # Verified against camoufox's own source (utils.py): config["navigator.userAgent"]
        # is the real override key, read back out via determine_ua_os().
        launch_options["config"] = {"navigator.userAgent": user_agent}

    with Camoufox(**launch_options) as browser:
        page = browser.new_page()
        session = PlaywrightBrowserSession(page)
        try:
            yield session
        finally:
            session.close()
            browser.close()
