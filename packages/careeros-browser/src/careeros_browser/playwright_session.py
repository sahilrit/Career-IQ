"""PlaywrightBrowserSession: the real BrowserSession implementation.

Playwright is free and open-source (Microsoft-maintained); it needs a
one-time local browser download (``uv run playwright install chromium``),
never a paid API key or hosted service. The wrapped ``page`` is typed as
``Any`` so this module works against anything exposing Playwright's
``Page`` surface — including a plain stub in tests — without requiring
the real ``playwright`` package to be importable just to read this code.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from careeros_browser.exceptions import (
    BrowserError,
    DownloadError,
    ResponseTimeoutError,
    SelectorTimeoutError,
)


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

    def press(self, selector: str, key: str) -> None:
        self._page.press(selector, key)

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

    def query_all(self, selector: str, *, extract: dict[str, str]) -> list[dict[str, str | None]]:
        results = []
        for element in self._page.query_selector_all(selector):
            row: dict[str, str | None] = {}
            for field_name, spec in extract.items():
                # "sub_selector@attribute" extracts an attribute (e.g. "a@href");
                # a bare selector (or "@attribute" alone) extracts text_content.
                sub_selector, _, attribute = spec.partition("@")
                sub_element = element.query_selector(sub_selector) if sub_selector else element
                if sub_element is None:
                    row[field_name] = None
                elif attribute:
                    row[field_name] = sub_element.get_attribute(attribute)
                else:
                    row[field_name] = sub_element.text_content()
            results.append(row)
        return results

    def capture_response_after(
        self,
        action: Callable[[], None],
        *,
        url_contains: str,
        timeout_ms: int = 10_000,
    ) -> str:
        try:
            with self._page.expect_response(
                lambda response: url_contains in response.url(), timeout=timeout_ms
            ) as response_info:
                action()
            return response_info.value.text()
        except Exception as exc:
            raise ResponseTimeoutError(
                f"No response containing {url_contains!r} within {timeout_ms}ms: {exc}"
            ) from exc

    def query_all_html(self, selector: str) -> list[str]:
        return self._page.eval_on_selector_all(selector, "els => els.map(el => el.outerHTML)")

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
        # Full page, not just the viewport — application forms sit below a long
        # job description, so a viewport shot shows only the blurb, not the
        # filled fields we want to review.
        self._page.screenshot(path=str(resolved), full_page=True)
        return resolved

    def user_agent(self) -> str:
        return self._page.evaluate("() => navigator.userAgent")

    def close(self) -> None:
        self._page.close()
