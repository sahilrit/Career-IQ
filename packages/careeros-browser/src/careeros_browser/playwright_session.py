"""PlaywrightBrowserSession: the real BrowserSession implementation.

Playwright is free and open-source (Microsoft-maintained); it needs a
one-time local browser download (``uv run playwright install chromium``),
never a paid API key or hosted service. The wrapped ``page`` is typed as
``Any`` so this module works against anything exposing Playwright's
``Page`` surface — including a plain stub in tests — without requiring
the real ``playwright`` package to be importable just to read this code.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from careeros_browser.exceptions import BrowserError, DownloadError, SelectorTimeoutError


class PlaywrightBrowserSession:
    """Wraps a Playwright ``Page`` behind the ``BrowserSession`` interface."""

    def __init__(self, page: Any) -> None:
        self._page = page

    def goto(self, url: str) -> None:
        try:
            self._page.goto(url)
        except Exception as exc:
            raise BrowserError(f"Failed to navigate to {url!r}: {exc}") from exc

    @property
    def current_url(self) -> str:
        return self._page.url

    def go_back(self) -> None:
        self._page.go_back()

    def get_cookies(self) -> list[dict]:
        return self._page.context.cookies()

    def set_cookie(self, cookie: dict) -> None:
        self._page.context.add_cookies([cookie])

    def clear_cookies(self) -> None:
        self._page.context.clear_cookies()

    def fill(self, selector: str, value: str) -> None:
        self._page.fill(selector, value)

    def click(self, selector: str) -> None:
        self._page.click(selector)

    def select_option(self, selector: str, value: str) -> None:
        self._page.select_option(selector, value)

    def upload_file(self, selector: str, file_path: str | Path) -> None:
        self._page.set_input_files(selector, str(file_path))

    def text_content(self, selector: str) -> str | None:
        return self._page.text_content(selector)

    def is_visible(self, selector: str) -> bool:
        return self._page.is_visible(selector)

    def wait_for_selector(self, selector: str, *, timeout_ms: int = 10_000) -> None:
        try:
            self._page.wait_for_selector(selector, timeout=timeout_ms)
        except Exception as exc:
            raise SelectorTimeoutError(
                f"Selector {selector!r} did not appear within {timeout_ms}ms"
            ) from exc

    def download_triggered_by(self, action, *, save_to: str | Path) -> Path:
        try:
            with self._page.expect_download() as download_info:
                action()
            download = download_info.value
            resolved = Path(save_to)
            download.save_as(str(resolved))
            return resolved
        except Exception as exc:
            raise DownloadError(f"Expected download never arrived: {exc}") from exc

    def screenshot(self, path: str | Path) -> Path:
        resolved = Path(path)
        self._page.screenshot(path=str(resolved))
        return resolved

    def close(self) -> None:
        self._page.close()
