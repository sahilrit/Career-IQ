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
    def press(self, selector: str, key: str) -> None:
        """Press a keyboard key while ``selector`` is focused.

        For forms with no reliably selectable submit button (a client-
        rendered login form whose submit control has no stable id/class),
        this is the robust way to submit — pressing Enter in the last
        filled field, exactly as a human would.
        """
        ...

    def select_option(self, selector: str, value: str) -> None: ...
    def upload_file(self, selector: str, file_path: str | Path) -> None: ...

    def text_content(self, selector: str) -> str | None: ...
    def is_visible(self, selector: str) -> bool: ...
    def wait_for_selector(self, selector: str, *, timeout_ms: int = 10_000) -> None: ...

    def capture_response_after(
        self,
        action: Callable[[], None],
        *,
        url_contains: str,
        timeout_ms: int = 10_000,
    ) -> str:
        """Run ``action`` and return the body of the first network response
        whose URL contains ``url_contains``.

        For sites whose search results arrive as JSON the page's own script
        fetches (Naukri's ``/jobapi/v3/search``), reading that response
        directly is far more robust than scraping the DOM the script renders
        from it — no dependency on rendered markup or timing.
        """
        ...

    def query_all_html(self, selector: str) -> list[str]:
        """The outer HTML of every element matching ``selector``.

        For markup too irregular for ``query_all``'s flat sub-selector
        map — label/value pairs (``<dt>Salary</dt><dd>...</dd>``), optional
        fields whose presence varies per card — this hands back real HTML
        so a plain ``html.parser`` function can do the extraction, the same
        pattern already used for HTML-based providers that fetch over
        plain HTTP.
        """
        ...

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

    def user_agent(self) -> str:
        """The live page's ``navigator.userAgent``.

        A site that ties a solved anti-bot challenge's cookies to the UA
        that solved it (e.g. Cloudflare's ``cf_clearance``) will reject a
        later plain-HTTP request made with a mismatched UA — this is how a
        caller reads back the real, possibly randomised, fingerprint a
        launcher (e.g. Camoufox) generated for the session, so subsequent
        requests outside the browser can reuse it exactly.
        """
        ...

    def close(self) -> None: ...
