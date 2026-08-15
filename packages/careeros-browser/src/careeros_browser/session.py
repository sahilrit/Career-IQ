"""BrowserSession: the abstraction every browser-driven capability in
CareerOS is built against.

Real websites that don't expose a useful free API (most job boards, most
freelance platforms) still expose a browser-usable UI — this is the
infrastructure for interacting with that UI without a paid
browser-automation SaaS. ``PlaywrightBrowserSession`` is the real
implementation; ``FakeBrowserSession`` is an in-memory test double any
later package can import instead of driving a real browser in tests.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol


class BrowserSession(Protocol):
    def goto(self, url: str) -> None: ...

    @property
    def current_url(self) -> str: ...

    def go_back(self) -> None: ...

    def get_cookies(self) -> list[dict]: ...
    def set_cookie(self, cookie: dict) -> None: ...
    def clear_cookies(self) -> None: ...

    def fill(self, selector: str, value: str) -> None: ...
    def click(self, selector: str) -> None: ...
    def select_option(self, selector: str, value: str) -> None: ...
    def upload_file(self, selector: str, file_path: str | Path) -> None: ...

    def text_content(self, selector: str) -> str | None: ...
    def is_visible(self, selector: str) -> bool: ...
    def wait_for_selector(self, selector: str, *, timeout_ms: int = 10_000) -> None: ...

    def query_all(self, selector: str, *, extract: dict[str, str]) -> list[dict[str, str | None]]:
        """Every element matching ``selector``, each rendered as a dict.

        ``extract`` maps output keys to sub-selectors evaluated relative
        to each matched element — the shape a search-results page (job
        listings, gig cards, ...) needs that a single ``text_content()``
        call can't give you. A sub-selector of the form
        ``"selector@attribute"`` (e.g. ``"a@href"``) extracts that
        attribute instead of the element's text; a bare ``"@attribute"``
        reads the attribute off the matched element itself.
        """
        ...

    def download_triggered_by(self, action: Callable[[], None], *, save_to: str | Path) -> Path: ...

    def screenshot(self, path: str | Path) -> Path: ...

    def close(self) -> None: ...
