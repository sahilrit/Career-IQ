"""FakeBrowserSession: an in-memory BrowserSession test double.

No real browser, no network, no Playwright required — every later
package that drives a "browser" in its test suite should use this
instead of launching Chromium, matching the project's no-network-in-
tests standard (see docs/development/standards.md).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from pathlib import Path

from careeros_browser.exceptions import (
    BrowserError,
    DownloadError,
    ResponseTimeoutError,
    SelectorTimeoutError,
)
from careeros_browser.frames import FrameHandle
from careeros_browser.matching import best_option_index


class FakeBrowserSession:
    def __init__(self) -> None:
        self._url = "about:blank"
        #: Nested documents, as (handle, session). A frame is modelled as a
        #: whole separate FakeBrowserSession because that is exactly what it is
        #: — a different document with its own elements and its own values —
        #: and it makes nesting free.
        self._frames: list[tuple[FrameHandle, FakeBrowserSession]] = []
        #: The <iframe> element selector each frame hangs off, in THIS document.
        self._frame_selectors: dict[str, FakeBrowserSession] = {}
        self._frame_path: tuple[str, ...] = ()
        self._history: list[str] = []
        self._cookies: list[dict] = []
        self._field_values: dict[str, str] = {}
        self._visible_selectors: set[str] = set()
        self._text_content: dict[str, str] = {}
        self._pending_download: Path | None = None
        self._query_all_results: dict[str, list[dict[str, str | None]]] = {}
        self._html_by_selector: dict[str, list[str]] = {}
        # Queued per url_contains pattern; capture_response_after pops one per
        # call, so a page that must be fetched twice needs two queued entries.
        self._queued_responses: dict[str, deque[str]] = {}
        self._failing_click_selectors: set[str] = set()
        #: Fields that silently DISCARD whatever is written to them - the
        #: React-controlled / disabled inputs that make a fill look successful
        #: while submitting nothing. Set via ``set_field_rejects``.
        self._rejecting_selectors: set[str] = set()
        #: Radio/checkbox controls currently ticked.
        self._checked: set[str] = set()
        #: Fields whose value cannot be read back at all.
        self._unreadable_selectors: set[str] = set()
        self._comboboxes: list[dict[str, str]] = []
        self._buttons: list[dict[str, object]] = []
        self._fields: list[dict[str, object]] = []
        self._combobox_options: dict[str, list[str]] = {}
        self.combobox_selections: list[tuple[str, str]] = []
        self._user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
        self.clicked_selectors: list[str] = []
        self.pressed_keys: list[tuple[str, str]] = []
        self.uploaded_files: dict[str, str] = {}
        self.screenshots_taken: list[Path] = []
        self.closed = False

    def goto(self, url: str) -> None:
        self._history.append(self._url)
        self._url = url

    @property
    def current_url(self) -> str:
        return self._url

    # -- frames --------------------------------------------------------------

    @property
    def frame_path(self) -> tuple[str, ...]:
        return self._frame_path

    def _flattened(self) -> list[tuple[FrameHandle, FakeBrowserSession]]:
        """Every frame below this one at ANY depth, outermost first.

        One traversal shared by ``frames()`` and ``frame(index=…)``, because
        Playwright's ``page.frames`` is likewise a FLAT list of every frame at
        any depth. Enumerating and indexing differently is how a test double
        starts lying: a form in a nested frame would be listed by ``frames()``
        and then unreachable by the index it was listed under.
        """
        found: list[tuple[FrameHandle, FakeBrowserSession]] = []
        for handle, session in self._frames:
            found.append((handle, session))
            for nested_handle, nested_session in session._flattened():
                found.append(
                    (
                        FrameHandle(
                            index=0,  # renumbered below
                            url=nested_handle.url,
                            name=nested_handle.name,
                            depth=handle.depth + nested_handle.depth,
                        ),
                        nested_session,
                    )
                )
        return [
            (
                FrameHandle(index=position, url=handle.url, name=handle.name, depth=handle.depth),
                session,
            )
            for position, (handle, session) in enumerate(found)
        ]

    def frames(self) -> list[FrameHandle]:
        """Every frame below this one, outermost first — depth included, so a
        nested frame is listed rather than hidden behind its parent."""
        return [handle for handle, _ in self._flattened()]

    def frame(
        self,
        *,
        url_contains: str | None = None,
        name: str | None = None,
        selector: str | None = None,
        index: int | None = None,
    ) -> FakeBrowserSession | None:
        if selector is not None:
            found = self._frame_selectors.get(selector)
            return self._scoped(found, f"selector={selector}") if found else None

        candidates = self._flattened()
        if index is not None:
            if not 0 <= index < len(candidates):
                return None
            return self._scoped(candidates[index][1], f"index={index}")
        for handle, session in candidates:
            if handle.matches(url_contains=url_contains, name=name):
                label = f"url~{url_contains}" if url_contains is not None else f"name={name}"
                return self._scoped(session, label)
        return None

    def _scoped(self, session: FakeBrowserSession, label: str) -> FakeBrowserSession:
        session._frame_path = (*self._frame_path, label)
        return session

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
        if selector in self._rejecting_selectors:
            # No exception: this is precisely the failure mode that read-back
            # verification exists to catch. A field that throws is easy; a
            # field that quietly keeps its old value is the dangerous one.
            return
        self._field_values[selector] = value

    def input_value(self, selector: str) -> str:
        if selector in self._unreadable_selectors:
            raise BrowserError(f"Could not read the value of {selector!r} (simulated)")
        return self._field_values.get(selector, "")

    def set_field_rejects(self, selector: str) -> None:
        """Make ``selector`` silently discard writes, like a React-controlled
        or disabled input does."""
        self._rejecting_selectors.add(selector)

    def set_field_unreadable(self, selector: str) -> None:
        self._unreadable_selectors.add(selector)

    def click(self, selector: str) -> None:
        if selector in self._failing_click_selectors:
            raise SelectorTimeoutError(f"Selector {selector!r} did not appear (simulated)")
        self.clicked_selectors.append(selector)

    def press(self, selector: str, key: str) -> None:
        self.pressed_keys.append((selector, key))

    def select_option(self, selector: str, value: str) -> None:
        self._field_values[selector] = value

    def choose(self, selector: str) -> None:
        if selector in self._rejecting_selectors:
            # Ticked nothing, raised nothing — the failure read-back exists for.
            return
        self._checked.add(selector)
        self.clicked_selectors.append(selector)

    def is_checked(self, selector: str) -> bool:
        return selector in self._checked

    def detect_comboboxes(self) -> list[dict[str, str]]:
        return [dict(row) for row in self._comboboxes]

    def detect_buttons(self) -> list[dict[str, object]]:
        return [dict(row) for row in self._buttons]

    def detect_fields(self) -> list[dict[str, object]]:
        return [dict(row) for row in self._fields]

    def select_combobox_option(self, control_selector: str, option_text: str) -> None:
        options = self._combobox_options.get(control_selector)
        if not options:
            raise BrowserError(f"Dropdown {control_selector!r} exposed no options to choose from")
        index = best_option_index(options, option_text)
        if index is None:
            raise BrowserError(
                f"No option matching {option_text!r} in dropdown {control_selector!r}"
            )
        chosen = options[index]
        self._field_values[control_selector] = chosen
        self.combobox_selections.append((control_selector, chosen))

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

    def capture_response_after(
        self,
        action: Callable[[], None],
        *,
        url_contains: str,
        timeout_ms: int = 10_000,
    ) -> str:
        # Mirrors PlaywrightBrowserSession: the whole navigate-or-click-then-
        # wait sequence is one operation, so a failure anywhere in it — the
        # action itself, or no matching response arriving — surfaces as one
        # error. A caller must not need to distinguish "the click failed"
        # from "the response never came"; both mean "this attempt failed".
        try:
            action()
            queue = self._queued_responses.get(url_contains)
            if not queue:
                raise ResponseTimeoutError(
                    f"No response queued for {url_contains!r} (call queue_response() in test setup)"
                )
            return queue.popleft()
        except ResponseTimeoutError:
            raise
        except Exception as exc:
            raise ResponseTimeoutError(
                f"Action failed before a response for {url_contains!r} arrived: {exc}"
            ) from exc

    def query_all_html(self, selector: str) -> list[str]:
        return list(self._html_by_selector.get(selector, []))

    def download_triggered_by(self, action: Callable[[], None], *, save_to: str | Path) -> Path:
        action()
        if self._pending_download is None:
            raise DownloadError("No download was queued (call queue_download() in test setup)")
        return self._pending_download

    def screenshot(self, path: str | Path) -> Path:
        resolved = Path(path)
        self.screenshots_taken.append(resolved)
        return resolved

    def user_agent(self) -> str:
        return self._user_agent

    def close(self) -> None:
        self.closed = True

    # --- test-only helpers, not part of the BrowserSession protocol ---

    def set_user_agent(self, user_agent: str) -> None:
        """Simulate the launcher having generated this fingerprint."""
        self._user_agent = user_agent

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

    def set_comboboxes(self, comboboxes: list[dict[str, str]]) -> None:
        """Simulate the page holding these custom dropdowns, for test setup."""
        self._comboboxes = [dict(row) for row in comboboxes]

    def set_buttons(self, buttons: list[dict[str, object]]) -> None:
        """Simulate the clickable controls on the page, for test setup.

        Keys mirror ``_DETECT_BUTTONS_JS``; anything omitted defaults, so a
        test only states the signals it is actually about.
        """
        self._buttons = [
            {
                "selector": "",
                "text": "",
                "accessible_name": "",
                "role": "button",
                "type": "",
                "disabled": False,
                "near_file_input": False,
                "in_form": True,
                "form_field_count": 0,
                "surrounding_text": "",
                "document_order": index,
                **row,
            }
            for index, row in enumerate(buttons)
        ]
        for row in self._buttons:
            selector = str(row.get("selector") or "")
            if selector:
                self._visible_selectors.add(selector)

    def set_fields(self, fields: list[dict[str, object]]) -> None:
        """Simulate the form fields on the page, for test setup. Keys mirror
        ``_DETECT_FIELDS_JS``."""
        self._fields = [
            {
                "selector": "",
                "tag": "input",
                "type": "text",
                "name": "",
                "id_attr": "",
                "label": "",
                "aria_label": "",
                "placeholder": "",
                "autocomplete": "",
                "heading": "",
                "required": False,
                "disabled": False,
                "readonly": False,
                "options": [],
                **row,
            }
            for row in fields
        ]
        for row in self._fields:
            selector = str(row.get("selector") or "")
            if selector:
                self._visible_selectors.add(selector)

    def set_combobox_options(self, control_selector: str, options: list[str]) -> None:
        """Simulate the options ``control_selector``'s dropdown offers once opened."""
        self._combobox_options[control_selector] = list(options)

    def set_html_blocks(self, selector: str, htmls: list[str]) -> None:
        """Simulate ``selector`` matching elements with this outer HTML."""
        self._html_by_selector[selector] = list(htmls)

    def set_click_failure(self, selector: str) -> None:
        """Simulate ``selector`` never appearing/being clickable — for
        testing "no more results / no next button" endings."""
        self._failing_click_selectors.add(selector)

    def add_frame(
        self,
        session: FakeBrowserSession | None = None,
        *,
        url: str = "",
        name: str = "",
        selector: str | None = None,
    ) -> FakeBrowserSession:
        """Nest a document inside this one, for test setup.

        Returns the frame's session so a test can set up its elements. Pass a
        session that already has frames of its own to build a nested case.
        """
        child = session if session is not None else FakeBrowserSession()
        child._url = url or child._url
        handle = FrameHandle(index=len(self._frames), url=url, name=name, depth=1)
        self._frames.append((handle, child))
        if selector:
            self._frame_selectors[selector] = child
            # The <iframe> element lives in THIS document, so a caller looking
            # for it with is_visible() must find it here.
            self._visible_selectors.add(selector)
        return child

    def queue_response(self, *, url_contains: str, body: str) -> None:
        """Queue a response body for the next matching capture_response_after
        call. Queue more than one to simulate pagination."""
        self._queued_responses.setdefault(url_contains, deque()).append(body)
