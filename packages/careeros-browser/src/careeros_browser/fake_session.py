"""FakeBrowserSession: an in-memory BrowserSession test double.

No real browser, no network, no Playwright required — every later
package that drives a "browser" in its test suite should use this
instead of launching Chromium, matching the project's no-network-in-
tests standard (see docs/development/standards.md).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from careeros_browser.exceptions import DownloadError, SelectorTimeoutError


class FakeBrowserSession:
    def __init__(self) -> None:
        self._url = "about:blank"
        self._history: list[str] = []
        self._cookies: list[dict] = []
        self._field_values: dict[str, str] = {}
        self._visible_selectors: set[str] = set()
        self._text_content: dict[str, str] = {}
        self._pending_download: Path | None = None
        self._query_all_results: dict[str, list[dict[str, str | None]]] = {}
        self.clicked_selectors: list[str] = []
        self.uploaded_files: dict[str, str] = {}
        self.screenshots_taken: list[Path] = []
        self.closed = False

    def goto(self, url: str) -> None:
        self._history.append(self._url)
        self._url = url

    @property
    def current_url(self) -> str:
        return self._url

    def go_back(self) -> None:
        if self._history:
            self._url = self._history.pop()

    def get_cookies(self) -> list[dict]:
        return list(self._cookies)

    def set_cookie(self, cookie: dict) -> None:
        self._cookies.append(cookie)

    def clear_cookies(self) -> None:
        self._cookies.clear()

    def fill(self, selector: str, value: str) -> None:
        self._field_values[selector] = value

    def click(self, selector: str) -> None:
        self.clicked_selectors.append(selector)

    def select_option(self, selector: str, value: str) -> None:
        self._field_values[selector] = value

    def upload_file(self, selector: str, file_path: str | Path) -> None:
        self.uploaded_files[selector] = str(file_path)

    def text_content(self, selector: str) -> str | None:
        return self._text_content.get(selector)

    def is_visible(self, selector: str) -> bool:
        return selector in self._visible_selectors

    def wait_for_selector(self, selector: str, *, timeout_ms: int = 10_000) -> None:
        if selector not in self._visible_selectors:
            raise SelectorTimeoutError(
                f"Selector {selector!r} did not appear within {timeout_ms}ms"
            )

    def query_all(self, selector: str, *, extract: dict[str, str]) -> list[dict[str, str | None]]:
        # `extract` describes the real sub-selector mapping a live browser
        # would use; the fake just replays whatever was queued for this
        # top-level selector via set_query_all_results().
        return list(self._query_all_results.get(selector, []))

    def download_triggered_by(self, action: Callable[[], None], *, save_to: str | Path) -> Path:
        action()
        if self._pending_download is None:
            raise DownloadError("No download was queued (call queue_download() in test setup)")
        return self._pending_download

    def screenshot(self, path: str | Path) -> Path:
        resolved = Path(path)
        self.screenshots_taken.append(resolved)
        return resolved

    def close(self) -> None:
        self.closed = True

    # --- test-only helpers, not part of the BrowserSession protocol ---

    def set_visible(self, selector: str, *, text: str | None = None) -> None:
        """Simulate an element becoming visible on the page, for test setup."""
        self._visible_selectors.add(selector)
        if text is not None:
            self._text_content[selector] = text

    def set_hidden(self, selector: str) -> None:
        """Simulate an element disappearing from the page, for test setup."""
        self._visible_selectors.discard(selector)

    def field_value(self, selector: str) -> str | None:
        return self._field_values.get(selector)

    def queue_download(self, path: str | Path) -> None:
        """Simulate the next action producing a download at ``path``."""
        self._pending_download = Path(path)

    def set_query_all_results(self, selector: str, results: list[dict[str, str | None]]) -> None:
        """Simulate ``selector`` matching a list of elements, for test setup."""
        self._query_all_results[selector] = results
