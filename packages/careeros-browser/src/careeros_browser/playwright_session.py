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
from careeros_browser.frames import FrameHandle
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


# Runs in the page: every clickable control with the signals a semantic
# classifier needs — accessible name, role, type, disabled state, form
# association, and whether it belongs to a file-upload widget. Reading these
# from the DOM is the only honest way to tell "Upload file" from "Submit
# Application" when both render as button[type=submit].
_DETECT_BUTTONS_JS = r"""
() => {
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return false;
    const s = getComputedStyle(el);
    return s.visibility !== 'hidden' && s.display !== 'none';
  };
  const textOf = (id) => {
    const n = id && document.getElementById(id);
    return n ? n.textContent.trim() : '';
  };
  // The accessible name, in the order a screen reader resolves it. This is
  // the single most reliable label for a control, and the reason a button
  // whose visible text is an icon can still be identified.
  const accessibleName = (el) => {
    const aria = (el.getAttribute('aria-label') || '').trim();
    if (aria) return aria;
    const lb = el.getAttribute('aria-labelledby');
    if (lb) {
      const t = lb.split(/\s+/).map(textOf).join(' ').trim();
      if (t) return t;
    }
    if (el.tagName === 'INPUT' && el.value) return String(el.value).trim();
    return (el.textContent || '').trim();
  };
  // Text near the control that is not its own label — the fieldset legend or
  // section heading that gives "Yes/No" buttons their meaning.
  const surrounding = (el) => {
    let p = el;
    for (let k = 0; k < 4 && p; k++) {
      p = p.parentElement;
      if (!p) break;
      const legend = p.querySelector('legend, h1, h2, h3, h4');
      if (legend && legend.textContent.trim()) return legend.textContent.trim().slice(0, 200);
    }
    return '';
  };
  const sel = "button, input[type='submit'], input[type='button'], [role='button']";
  const out = [];
  let stamp = 0;
  for (const el of Array.from(document.querySelectorAll(sel))) {
    if (!visible(el)) continue;
    if (!el.id) el.id = 'cos-btn-' + (stamp++);
    const form = el.form || el.closest('form');
    // Is this control part of a file-upload WIDGET — a small wrapper holding
    // a file input and its button — as opposed to merely sharing a <form>
    // with one? The distinction matters: on a simple one-column form the
    // button and the CV field share a parent within two hops, and treating
    // that as an upload widget classified "Apply for this job" as an upload
    // button and lost the form entirely.
    //
    // So: stop at form/fieldset boundaries, and only count a container that
    // holds at most two form controls. A real upload widget is small; a form
    // is not.
    let wrapper = el.parentElement;
    let nearFileInput = false;
    for (let k = 0; k < 3 && wrapper; k++) {
      const tag = wrapper.tagName;
      if (tag === 'FORM' || tag === 'FIELDSET' || tag === 'BODY') break;
      if (wrapper.querySelector("input[type='file']")) {
        const controls = wrapper.querySelectorAll('input, textarea, select').length;
        if (controls <= 2) { nearFileInput = true; }
        break;
      }
      wrapper = wrapper.parentElement;
    }
    out.push({
      selector: '[id="' + el.id + '"]',
      text: (el.textContent || '').trim().slice(0, 120),
      accessible_name: accessibleName(el).slice(0, 120),
      role: (el.getAttribute('role') || el.tagName.toLowerCase()),
      type: (el.getAttribute('type') || ''),
      disabled: !!(el.disabled || el.getAttribute('aria-disabled') === 'true'),
      near_file_input: nearFileInput,
      in_form: !!form,
      form_field_count: form ? form.querySelectorAll('input, textarea, select').length : 0,
      surrounding_text: surrounding(el),
      document_order: out.length,
    });
  }
  return out;
}
"""


# Runs in the page: every visible form field with ALL of its label signals,
# not just the one this ATS happens to use. Real forms label a field by
# <label for>, by a wrapping <label>, by aria-label, by aria-labelledby, by
# placeholder, or by nothing but a nearby heading — and different ATSes pick
# different ones. Collecting them all here means the mapper decides from
# evidence rather than from a guess about which convention this site follows.
_DETECT_FIELDS_JS = r"""
() => {
  const visible = (el) => {
    if (el.type === 'hidden') return false;
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return false;
    const s = getComputedStyle(el);
    return s.visibility !== 'hidden' && s.display !== 'none';
  };
  const textOf = (id) => {
    const n = id && document.getElementById(id);
    return n ? n.textContent.trim() : '';
  };
  // A label that WRAPS its control also contains that control's text — and a
  // <select>'s text is every one of its options. Taking textContent straight
  // off it produced questions like
  //   "genderselect ...malefemaledecline to self-identify"
  // which is unreadable to a human and unanswerable by a model. Strip the
  // form controls out of a copy before reading it.
  const cleanText = (node) => {
    if (!node) return '';
    const copy = node.cloneNode(true);
    copy.querySelectorAll('input, select, textarea, option, button').forEach(
      (n) => n.remove()
    );
    return copy.textContent.replace(/\s+/g, ' ').trim();
  };
  const labelText = (el) => {
    if (el.id) {
      // CSS.escape: ATS ids are often all-numeric, and '#4001209002' is
      // INVALID CSS — the unescaped form threw and lost the label entirely.
      const sel = 'label[for="' + (window.CSS && CSS.escape ? CSS.escape(el.id) : el.id) + '"]';
      let lab = null;
      try { lab = document.querySelector(sel); } catch (e) { lab = null; }
      if (lab && cleanText(lab)) return cleanText(lab);
    }
    const own = el.closest('label');
    if (own && cleanText(own)) return cleanText(own);
    // React form libraries put the <label> on the field WRAPPER, several
    // levels above the input itself.
    let p = el;
    for (let k = 0; k < 4 && p; k++) {
      p = p.parentElement;
      if (!p) break;
      const lab = p.querySelector('label');
      if (lab && cleanText(lab)) return cleanText(lab);
    }
    return '';
  };
  const ariaName = (el) => {
    const aria = (el.getAttribute('aria-label') || '').trim();
    if (aria) return aria;
    const lb = el.getAttribute('aria-labelledby');
    if (lb) return lb.split(/\s+/).map(textOf).join(' ').trim();
    return '';
  };
  const heading = (el) => {
    let p = el;
    for (let k = 0; k < 4 && p; k++) {
      p = p.parentElement;
      if (!p) break;
      const h = p.querySelector('legend, h1, h2, h3, h4');
      if (h && h.textContent.trim()) return h.textContent.trim().slice(0, 200);
    }
    return '';
  };
  // A radio/checkbox's own label names an OPTION ("Yes", "Decline to
  // self-identify"), not a question. The question is the group's legend or
  // heading. Reporting each option as its own field turned one EEO question
  // into eleven unanswerable required ones — and then tried to TEXT-FILL a
  // radio, which throws.
  const groupLabel = (el) => {
    const fieldset = el.closest('fieldset');
    const legend = fieldset && fieldset.querySelector('legend');
    if (legend && legend.textContent.trim()) return legend.textContent.trim();
    const group = el.closest("[role='radiogroup'], [role='group']");
    const aria = group && (group.getAttribute('aria-label') || '').trim();
    if (aria) return aria;
    const h = heading(el);
    if (h) return h;
    // Neither a <fieldset>/<legend> nor a heading. Lever renders a question as
    // plain divs — <div class="application-label">Are you authorized…</div>
    // wrapping the radios — so the group label fell back to the first OPTION,
    // and the question came out as literally "no". Unanswerable, and then
    // blocking because the form marks it required.
    //
    // Walk up to the smallest ancestor that holds the WHOLE group, then read
    // its text with the controls and their option labels removed. What is left
    // is the question.
    const name = el.getAttribute('name');
    if (name) {
      const escaped = window.CSS && CSS.escape ? CSS.escape(name) : name;
      let p = el.parentElement;
      for (let k = 0; k < 6 && p; k++) {
        const inGroup = p.querySelectorAll('input[name="' + escaped + '"]').length;
        if (inGroup > 1) {
          // Keep ASCENDING while the text is empty. The tightest ancestor that
          // holds the whole group is usually just the options wrapper
          // (<div class="application-field">) — the question text sits in a
          // sibling one level up. Stopping at the first group-containing
          // ancestor found nothing and fell back to the option label.
          const copy = p.cloneNode(true);
          copy.querySelectorAll('input, select, textarea, option, button, label').forEach(
            (n) => n.remove()
          );
          const text = copy.textContent.replace(/\s+/g, ' ').trim();
          if (text) return text.slice(0, 200);
        }
        p = p.parentElement;
      }
    }
    return '';
  };
  const out = [];
  let stamp = 0;
  for (const el of Array.from(document.querySelectorAll('input, textarea, select'))) {
    if (!visible(el)) continue;
    if (!el.id) el.id = 'cos-fld-' + (stamp++);
    const tag = el.tagName.toLowerCase();
    const rawType = (el.getAttribute('type') || '').toLowerCase();
    const isChoice = rawType === 'radio' || rawType === 'checkbox';
    const ownLabel = labelText(el);
    const label = isChoice ? (groupLabel(el) || ownLabel) : ownLabel;
    const required = !!(el.required || el.getAttribute('aria-required') === 'true' ||
                        /\*|\(required\)/i.test(label));
    out.push({
      // Attribute selector, never '#id': all-numeric ids are legal HTML and
      // invalid CSS, and '#4001209002' throws when filled.
      selector: '[id="' + el.id + '"]',
      tag: tag,
      type: (el.getAttribute('type') || (tag === 'textarea' ? 'textarea' : tag)).toLowerCase(),
      name: (el.getAttribute('name') || ''),
      id_attr: el.id,
      label: label,
      aria_label: ariaName(el),
      placeholder: (el.getAttribute('placeholder') || ''),
      autocomplete: (el.getAttribute('autocomplete') || ''),
      heading: heading(el),
      required: required,
      disabled: !!el.disabled,
      readonly: !!el.readOnly,
      // What this one control offers, and which group it belongs to. The
      // caller collapses a group into a single question.
      option_label: isChoice ? ownLabel : '',
      group_name: isChoice ? (el.getAttribute('name') || label) : '',
      options: tag === 'select'
        ? Array.from(el.options).map((o) => (o.textContent || '').trim()).slice(0, 40)
        : [],
    });
  }
  return out;
}
"""


class PlaywrightBrowserSession:
    """Wraps a Playwright ``Page`` behind the ``BrowserSession`` interface.

    Element operations go through ``_target``, which is the page itself for a
    normal session and a ``Frame`` for one returned by ``frame()``. Playwright
    gives ``Page`` and ``Frame`` the same element surface, so scoping to a
    frame costs nothing but the indirection — and everything above this class
    (form detection, mapping, filling, read-back) works inside an iframe
    without knowing it is in one.

    Page-level operations — cookies, screenshots, downloads, closing — always
    use ``_page``, because a frame does not have them and a frame session must
    still be able to screenshot the page it lives on.
    """

    def __init__(
        self,
        page: Any,
        *,
        target: Any | None = None,
        frame_path: tuple[str, ...] = (),
    ) -> None:
        self._page = page
        self._target = page if target is None else target
        self._frame_path = tuple(frame_path)

    # -- frames --------------------------------------------------------------

    @property
    def frame_path(self) -> tuple[str, ...]:
        return self._frame_path

    def _child_frames(self) -> list[Any]:
        """Frames below ``_target``, outermost first.

        ``page.frames`` is a flat list of every frame at any depth including
        the main one, so for a page session we drop the main frame and keep
        the rest; for a frame session we walk that frame's own subtree.
        """
        if self._target is self._page:
            try:
                main = self._page.main_frame
            except Exception:
                main = None
            try:
                return [f for f in (self._page.frames or []) if f is not main]
            except Exception:
                return []
        collected: list[Any] = []
        pending = list(getattr(self._target, "child_frames", None) or [])
        while pending:
            frame = pending.pop(0)
            collected.append(frame)
            pending.extend(list(getattr(frame, "child_frames", None) or []))
        return collected

    @staticmethod
    def _depth_of(frame: Any) -> int:
        depth = 0
        current = frame
        while current is not None:
            parent = getattr(current, "parent_frame", None)
            if callable(parent):
                parent = parent()
            if parent is None:
                break
            depth += 1
            current = parent
        return max(depth, 1)

    def frames(self) -> list[FrameHandle]:
        handles: list[FrameHandle] = []
        for index, frame in enumerate(self._child_frames()):
            handles.append(
                FrameHandle(
                    index=index,
                    url=getattr(frame, "url", "") or "",
                    name=getattr(frame, "name", "") or "",
                    depth=self._depth_of(frame),
                )
            )
        return handles

    def _frame_from_selector(self, selector: str) -> Any | None:
        """The frame belonging to the ``<iframe>`` element at ``selector``.

        Resolved through the element rather than by URL because that is the
        only way to pick a specific one when a page embeds several frames
        from the same origin.
        """
        try:
            element = self._target.query_selector(selector)
        except Exception:
            return None
        if element is None:
            return None
        try:
            return element.content_frame()
        except Exception:
            return None

    def frame(
        self,
        *,
        url_contains: str | None = None,
        name: str | None = None,
        selector: str | None = None,
        index: int | None = None,
    ) -> PlaywrightBrowserSession | None:
        if selector is not None:
            found = self._frame_from_selector(selector)
            return None if found is None else self._scoped(found, f"selector={selector}")

        candidates = self._child_frames()
        if index is not None:
            if not 0 <= index < len(candidates):
                return None
            return self._scoped(candidates[index], f"index={index}")

        for candidate in candidates:
            handle = FrameHandle(
                index=0,
                url=getattr(candidate, "url", "") or "",
                name=getattr(candidate, "name", "") or "",
            )
            if handle.matches(url_contains=url_contains, name=name):
                label = f"url~{url_contains}" if url_contains is not None else f"name={name}"
                return self._scoped(candidate, label)
        return None

    def _scoped(self, frame: Any, label: str) -> PlaywrightBrowserSession:
        return PlaywrightBrowserSession(
            self._page, target=frame, frame_path=(*self._frame_path, label)
        )

    # -- navigation and page-level state -------------------------------------

    def goto(self, url: str) -> None:
        try:
            self._page.goto(url)
        except Exception as exc:
            raise BrowserError(f"Failed to navigate to {url!r}: {exc}") from exc

    @property
    def current_url(self) -> str:
        # A frame session reports its OWN document's URL: that is what its
        # selectors resolve against, and reporting the page URL there would
        # make an evidence trail describe the wrong document.
        return self._target.url if self._target is not self._page else self._page.url

    def go_back(self) -> None:
        self._page.go_back()

    def get_cookies(self) -> list[dict]:
        return self._page.context.cookies()

    def set_cookie(self, cookie: dict) -> None:
        self._page.context.add_cookies([cookie])

    def clear_cookies(self) -> None:
        self._page.context.clear_cookies()

    # -- elements (scoped to _target) ----------------------------------------

    def fill(self, selector: str, value: str) -> None:
        self._target.fill(selector, value)

    def click(self, selector: str) -> None:
        self._target.click(selector)

    def press(self, selector: str, key: str) -> None:
        self._target.press(selector, key)

    #: Setting a <select> is instant or it is not going to work. Playwright's
    #: 30s default meant one select that never accepts a value cost half a
    #: minute, and a form with several of them spent minutes failing — the
    #: same reasoning as COMBOBOX_CLICK_TIMEOUT_MS below.
    SELECT_OPTION_TIMEOUT_MS = 5_000

    def select_option(self, selector: str, value: str) -> None:
        self._target.select_option(selector, value, timeout=self.SELECT_OPTION_TIMEOUT_MS)

    def choose(self, selector: str) -> None:
        # check() rather than click(): it is idempotent, and it fails loudly on
        # a control that is not actually checkable instead of clicking whatever
        # happens to be under the coordinates.
        self._target.check(selector)

    def is_checked(self, selector: str) -> bool:
        try:
            return bool(self._target.is_checked(selector))
        except Exception as exc:
            raise BrowserError(f"Could not read the state of {selector!r}: {exc}") from exc

    def input_value(self, selector: str) -> str:
        try:
            return self._target.input_value(selector)
        except Exception as exc:
            raise BrowserError(f"Could not read the value of {selector!r}: {exc}") from exc

    def detect_buttons(self) -> list[dict[str, object]]:
        """Every visible clickable control, with the signals needed to tell
        what it actually does. See ``_DETECT_BUTTONS_JS``."""
        try:
            found = self._target.evaluate(_DETECT_BUTTONS_JS)
        except Exception:
            return []
        return [dict(row) for row in (found or []) if isinstance(row, dict)]

    def detect_fields(self) -> list[dict[str, object]]:
        """Every visible form field, with every label signal the page offers.

        One DOM pass rather than a dozen speculative selector probes: the
        caller decides what each field IS from the signals, instead of hoping
        one of a hardcoded list of selectors happens to match this ATS.
        """
        try:
            found = self._target.evaluate(_DETECT_FIELDS_JS)
        except Exception:
            return []
        return [dict(row) for row in (found or []) if isinstance(row, dict)]

    def detect_comboboxes(self) -> list[dict[str, str]]:
        try:
            found = self._target.evaluate(_DETECT_COMBOBOXES_JS)
        except Exception:
            return []
        results: list[dict[str, str]] = []
        for row in found or []:
            selector = (row.get("selector") or "").strip()
            question = (row.get("question") or "").strip()
            if selector and question:
                results.append({"selector": selector, "question": question})
        return results

    #: Opening a dropdown is a two-second operation or it is not going to work.
    #: Playwright's 30s default meant one readonly combobox that never accepts a
    #: click cost half a minute per field, and a form with several of them
    #: could spend minutes failing.
    COMBOBOX_CLICK_TIMEOUT_MS = 5_000

    def select_combobox_option(self, control_selector: str, option_text: str) -> None:
        page = self._target
        # Open the menu. Clicking the control focuses it and (for react-select /
        # ARIA comboboxes) renders the option list.
        try:
            page.click(control_selector, timeout=self.COMBOBOX_CLICK_TIMEOUT_MS)
        except Exception as exc:
            raise BrowserError(
                f"Dropdown {control_selector!r} could not be opened: {str(exc).splitlines()[0]}"
            ) from exc
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
        self._target.set_input_files(selector, str(file_path))

    def text_content(self, selector: str) -> str | None:
        return self._target.text_content(selector)

    def is_visible(self, selector: str) -> bool:
        return self._target.is_visible(selector)

    def wait_for_selector(self, selector: str, *, timeout_ms: int = 10_000) -> None:
        try:
            self._target.wait_for_selector(selector, timeout=timeout_ms)
        except Exception as exc:
            raise SelectorTimeoutError(
                f"Selector {selector!r} did not appear within {timeout_ms}ms"
            ) from exc

    def query_all(self, selector: str, *, extract: dict[str, str]) -> list[dict[str, str | None]]:
        results = []
        for element in self._target.query_selector_all(selector):
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
        return self._target.eval_on_selector_all(selector, "els => els.map(el => el.outerHTML)")

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
