"""PlaywrightBrowserSession: the real BrowserSession implementation.

Playwright is free and open-source (Microsoft-maintained); it needs a
one-time local browser download (``uv run playwright install chromium``),
never a paid API key or hosted service. The wrapped ``page`` is typed as
``Any`` so this module works against anything exposing Playwright's
``Page`` surface — including a plain stub in tests — without requiring
the real ``playwright`` package to be importable just to read this code.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

from careeros_browser.exceptions import (
    BrowserError,
    DownloadError,
    ResponseTimeoutError,
    SelectorTimeoutError,
)
from careeros_browser.matching import best_option_index

# Runs in the page: find every custom (React/ARIA) dropdown, resolve its
# question label, stamp a stable id on its clickable control, and hand back
# {selector, question}. It walks up to a few ancestors for the label because
# React dropdowns put the <label for=…> on the field WRAPPER, not on the tiny
# combobox input inside it — the reason a plain [label for] scrape found none.
_DETECT_COMBOBOXES_JS = r"""
() => {
  const STANDARD = ['first name','last name','full name','email','phone',
                    'resume','cv','cover letter'];
  const textOf = (id) => {
    const n = id && document.getElementById(id);
    return n ? n.textContent.trim() : '';
  };
  const labelFor = (el) => {
    const aria = (el.getAttribute('aria-label') || '').trim();
    if (aria) return aria;
    const lb = el.getAttribute('aria-labelledby');
    if (lb) { const t = lb.split(/\s+/).map(textOf).join(' ').trim(); if (t) return t; }
    const own = el.closest('label');
    if (own && own.textContent.trim()) return own.textContent.trim();
    let p = el;
    for (let k = 0; k < 5 && p; k++) {
      p = p.parentElement;
      if (!p) break;
      const lab = p.querySelector('label');
      if (lab && lab.textContent.trim()) return lab.textContent.trim();
    }
    return '';
  };
  // react-select exposes its options input as [role=combobox]; other ATS use a
  // role=combobox div. Both are covered; native <select> is intentionally NOT.
  const sel = "[role='combobox'], input[id^='react-select']";
  const nodes = Array.from(document.querySelectorAll(sel));
  const out = [];
  const seen = new Set();
  let stamp = 0;
  for (const el of nodes) {
    const question = labelFor(el);
    if (!question) continue;
    const lowered = question.toLowerCase();
    if (STANDARD.some((w) => lowered.includes(w))) continue;
    if (!el.id) el.id = 'cos-combo-' + (stamp++);
    const selector = '[id="' + el.id + '"]';
    if (seen.has(selector)) continue;
    seen.add(selector);
    out.push({ selector, question });
  }
  return out;
}
"""


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

    def input_value(self, selector: str) -> str:
        try:
            return self._page.input_value(selector)
        except Exception as exc:
            raise BrowserError(f"Could not read the value of {selector!r}: {exc}") from exc

    def detect_comboboxes(self) -> list[dict[str, str]]:
        try:
            found = self._page.evaluate(_DETECT_COMBOBOXES_JS)
        except Exception:
            return []
        results: list[dict[str, str]] = []
        for row in found or []:
            selector = (row.get("selector") or "").strip()
            question = (row.get("question") or "").strip()
            if selector and question:
                results.append({"selector": selector, "question": question})
        return results

    def select_combobox_option(self, control_selector: str, option_text: str) -> None:
        page = self._page
        # Open the menu. Clicking the control focuses it and (for react-select /
        # ARIA comboboxes) renders the option list.
        page.click(control_selector)
        # Best-effort type-to-filter: react-select narrows a long list as you
        # type, which makes the right option render even when the list is
        # virtualised. Harmless (and ignored) on dropdowns that aren't inputs.
        with contextlib.suppress(Exception):
            page.fill(control_selector, option_text)
        # Wait for options to appear; if they never do this isn't an
        # options-list dropdown we can drive — raise so the field is left blank.
        try:
            page.wait_for_selector("[role='option']", timeout=3000)
        except Exception as exc:
            raise BrowserError(
                f"Dropdown {control_selector!r} exposed no options to choose from"
            ) from exc
        handles = page.query_selector_all("[role='option']")
        visible: list[Any] = []
        texts: list[str] = []
        for handle in handles:
            try:
                if handle.is_visible():
                    visible.append(handle)
                    texts.append((handle.text_content() or "").strip())
            except Exception:
                continue
        index = best_option_index(texts, option_text)
        if index is None:
            raise BrowserError(
                f"No option matching {option_text!r} in dropdown {control_selector!r} "
                f"(options: {texts})"
            )
        visible[index].click()

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
