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

from careeros_browser.frames import FrameHandle


class BrowserSession(Protocol):
    def goto(self, url: str) -> None: ...

    # -- frames --------------------------------------------------------------
    #
    # A CSS selector only ever reaches one document, so an <iframe> is not
    # "harder to select" — it is unreachable. Being able to scope a session to
    # a frame is what makes an ATS that renders its form in an iframe work at
    # all, and it makes it work for every caller at once rather than needing a
    # per-site workaround.

    def frames(self) -> list[FrameHandle]:
        """Every frame nested below this session, outermost first.

        Empty on an ordinary page, so callers pay nothing for asking.
        """
        ...

    def frame(
        self,
        *,
        url_contains: str | None = None,
        name: str | None = None,
        selector: str | None = None,
        index: int | None = None,
    ) -> BrowserSession | None:
        """A session scoped to one frame, or None if no frame matches.

        Identify it by document URL fragment, frame name, the ``<iframe>``
        element's selector in THIS document, or position. The returned object
        is a full ``BrowserSession``: fill, read back, detect comboboxes and
        list further frames all work inside it, so nesting needs no extra
        concept and existing callers need no changes.
        """
        ...

    @property
    def frame_path(self) -> tuple[str, ...]:
        """How this session was reached from the page, for diagnostics.

        Empty for the main document. Without it, "the field was not filled"
        cannot be told apart from "the field was not filled *in the frame we
        were looking at*", which is a genuinely different bug.
        """
        ...

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

    def choose(self, selector: str) -> None:
        """Tick the radio/checkbox at ``selector``.

        Separate from ``fill`` because a choice control is not written to — a
        programmatic ``fill`` on one raises, which is exactly how eleven EEO
        radio buttons turned into eleven failed fields.
        """
        ...

    def is_checked(self, selector: str) -> bool:
        """Whether the choice control at ``selector`` is now ticked.

        The read-back half: clicking a radio inside a custom widget can be
        intercepted and do nothing, which looks identical to success.
        """
        ...

    def input_value(self, selector: str) -> str:
        """The value currently IN the field — what the page would submit.

        Filling a form is not the same as having filled it. A React-controlled
        input can reject or rewrite a programmatic value, a disabled field
        silently ignores one, and a field that scrolled out of an accordion may
        never have received it. Reading the value back is the only way to tell
        a fill that worked from one that looked like it did, which is the
        difference between an application that submits and one that bounces.

        Returns "" when the field has no value; raises when the selector does
        not resolve.
        """
        ...

    def detect_buttons(self) -> list[dict[str, object]]:
        """Every visible clickable control, with the signals that say what it
        actually does: accessible name, role, type, disabled state, form
        association, and whether it belongs to a file-upload widget.

        Existence of this method is why the final submit control is chosen by
        what it IS rather than by a selector that happens to match. On a real
        Ashby form forty controls match ``button[type=submit]`` — every
        "Upload file" and every Yes/No option among them — so a selector alone
        cannot tell the button that sends the application from the one that
        opens a file dialog.
        """
        ...

    def detect_fields(self) -> list[dict[str, object]]:
        """Every visible form field with ALL of its label signals — ``<label
        for>``, wrapping label, aria-label, aria-labelledby, placeholder,
        autocomplete, nearby heading, type, and select options.

        Different ATSes label fields in different ways, so a mapper that reads
        only one signal works on some sites and silently mis-maps on others.
        """
        ...

    def detect_comboboxes(self) -> list[dict[str, str]]:
        """Custom (React/ARIA) dropdowns on the page — the ``Select…`` widgets
        that are NOT native ``<select>`` elements and so can't be filled with
        ``select_option``.

        Returns one ``{"selector": ..., "question": ...}`` per dropdown: a
        stable selector for the clickable control, and the question label
        resolved from its ``aria-label``/``<label>``. Native ``<select>`` and
        the standard name/email/phone fields are excluded. Empty when the page
        has none (the common case), so callers pay nothing on plain forms.
        """
        ...

    def select_combobox_option(self, control_selector: str, option_text: str) -> None:
        """Open the custom dropdown at ``control_selector`` and choose the
        option best matching ``option_text``.

        Raises if the dropdown never opens or no option matches — the caller
        then leaves the field for a human rather than picking a wrong value.
        """
        ...

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
