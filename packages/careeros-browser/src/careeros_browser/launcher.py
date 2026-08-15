"""Launches real Playwright browser sessions.

Requires the ``playwright`` package (already a dependency) and its
browser binaries, installed once, locally, for free via
``uv run playwright install chromium`` — never a paid step and never
required just to import this module.
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
