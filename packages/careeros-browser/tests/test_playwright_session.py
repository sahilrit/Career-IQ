"""Tests for PlaywrightBrowserSession's delegation logic, against a plain
stub standing in for playwright.sync_api.Page — no real browser or the
playwright browser binaries required.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from careeros_browser import BrowserError, DownloadError, PlaywrightBrowserSession


class _StubContext:
    def __init__(self) -> None:
        self._cookies: list[dict] = []

    def cookies(self) -> list[dict]:
        return list(self._cookies)

    def add_cookies(self, cookies: list[dict]) -> None:
        self._cookies.extend(cookies)

    def clear_cookies(self) -> None:
        self._cookies.clear()


class _StubDownload:
    def __init__(self, path: Path) -> None:
        self._path = path
        self.saved_to: str | None = None

    def save_as(self, path: str) -> None:
        self.saved_to = path


class _DownloadInfo:
    def __init__(self, download: _StubDownload) -> None:
        self.value = download

    def __enter__(self) -> _DownloadInfo:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None


class _StubElement:
    def __init__(
        self,
        text: str = "",
        attributes: dict[str, str] | None = None,
        children: dict[str, _StubElement] | None = None,
    ) -> None:
        self._text = text
        self._attributes = attributes or {}
        self._children = children or {}

    def query_selector(self, selector: str) -> _StubElement | None:
        return self._children.get(selector)

    def text_content(self) -> str:
        return self._text

    def get_attribute(self, name: str) -> str | None:
        return self._attributes.get(name)


class _StubPage:
    def __init__(self) -> None:
        self.url = "about:blank"
        self.context = _StubContext()
        self.calls: list[tuple] = []
        self._download: _StubDownload | None = None
        self._elements_by_selector: dict[str, list[_StubElement]] = {}
        self.closed = False

    def set_query_selector_all(self, selector: str, elements: list[_StubElement]) -> None:
        self._elements_by_selector[selector] = elements

    def query_selector_all(self, selector: str) -> list[_StubElement]:
        return self._elements_by_selector.get(selector, [])

    def goto(self, url: str) -> None:
        self.calls.append(("goto", url))
        self.url = url

    def go_back(self) -> None:
        self.calls.append(("go_back",))

    def fill(self, selector: str, value: str) -> None:
        self.calls.append(("fill", selector, value))

    def click(self, selector: str) -> None:
        self.calls.append(("click", selector))

    def select_option(self, selector: str, value: str) -> None:
        self.calls.append(("select_option", selector, value))

    def set_input_files(self, selector: str, path: str) -> None:
        self.calls.append(("set_input_files", selector, path))

    def text_content(self, selector: str) -> str:
        return f"text-of-{selector}"

    def is_visible(self, selector: str) -> bool:
        return selector == "#visible"

    def wait_for_selector(self, selector: str, timeout: int) -> None:
        if selector == "#missing":
            raise TimeoutError("not found")

    def expect_download(self) -> _DownloadInfo:
        if self._download is None:
            raise RuntimeError("no download queued")
        return _DownloadInfo(self._download)

    def queue_download(self, path: Path) -> None:
        self._download = _StubDownload(path)

    def screenshot(self, path: str) -> None:
        self.calls.append(("screenshot", path))

    def close(self) -> None:
        self.closed = True


def test_goto_delegates_and_wraps_errors():
    page = _StubPage()
    session = PlaywrightBrowserSession(page)
    session.goto("https://example.com")
    assert session.current_url == "https://example.com"


def test_goto_failure_raises_browser_error():
    class FailingPage(_StubPage):
        def goto(self, url: str) -> None:
            raise RuntimeError("network down")

    session = PlaywrightBrowserSession(FailingPage())
    with pytest.raises(BrowserError):
        session.goto("https://example.com")


def test_cookies_delegate_to_the_page_context():
    page = _StubPage()
    session = PlaywrightBrowserSession(page)
    session.set_cookie({"name": "a", "value": "1"})
    assert session.get_cookies() == [{"name": "a", "value": "1"}]
    session.clear_cookies()
    assert session.get_cookies() == []


def test_fill_click_and_select_option_delegate():
    page = _StubPage()
    session = PlaywrightBrowserSession(page)
    session.fill("#email", "ada@example.com")
    session.click("#submit")
    session.select_option("#country", "US")
    assert ("fill", "#email", "ada@example.com") in page.calls
    assert ("click", "#submit") in page.calls
    assert ("select_option", "#country", "US") in page.calls


def test_upload_file_delegates_to_set_input_files():
    page = _StubPage()
    session = PlaywrightBrowserSession(page)
    session.upload_file("#resume", "/tmp/resume.pdf")
    assert ("set_input_files", "#resume", "/tmp/resume.pdf") in page.calls


def test_is_visible_and_text_content_delegate():
    page = _StubPage()
    session = PlaywrightBrowserSession(page)
    assert session.is_visible("#visible") is True
    assert session.is_visible("#hidden") is False
    assert session.text_content("#hidden") == "text-of-#hidden"


def test_wait_for_selector_raises_selector_timeout_on_failure():
    from careeros_browser import SelectorTimeoutError

    page = _StubPage()
    session = PlaywrightBrowserSession(page)
    with pytest.raises(SelectorTimeoutError):
        session.wait_for_selector("#missing", timeout_ms=50)


def test_download_triggered_by_saves_and_returns_the_path():
    page = _StubPage()
    page.queue_download(Path("/tmp/original.pdf"))
    session = PlaywrightBrowserSession(page)

    result = session.download_triggered_by(lambda: None, save_to="/tmp/saved.pdf")

    assert result == Path("/tmp/saved.pdf")


def test_download_triggered_by_without_a_download_raises():
    page = _StubPage()
    session = PlaywrightBrowserSession(page)
    with pytest.raises(DownloadError):
        session.download_triggered_by(lambda: None, save_to="/tmp/saved.pdf")


def test_screenshot_delegates_and_returns_path():
    page = _StubPage()
    session = PlaywrightBrowserSession(page)
    result = session.screenshot("/tmp/shot.png")
    assert result == Path("/tmp/shot.png")
    assert ("screenshot", "/tmp/shot.png") in page.calls


def test_close_delegates():
    page = _StubPage()
    session = PlaywrightBrowserSession(page)
    session.close()
    assert page.closed is True


def test_query_all_extracts_text_and_href_per_element():
    card = _StubElement(
        children={
            ".title": _StubElement(text="Senior Engineer"),
            "a": _StubElement(attributes={"href": "https://example.com/1"}),
        }
    )
    page = _StubPage()
    page.set_query_selector_all(".gig-card", [card])
    session = PlaywrightBrowserSession(page)

    result = session.query_all(".gig-card", extract={"title": ".title", "url": "a@href"})

    assert result == [{"title": "Senior Engineer", "url": "https://example.com/1"}]


def test_query_all_returns_one_row_per_matched_element():
    cards = [_StubElement(children={".title": _StubElement(text=f"Gig {i}")}) for i in range(3)]
    page = _StubPage()
    page.set_query_selector_all(".gig-card", cards)
    session = PlaywrightBrowserSession(page)

    result = session.query_all(".gig-card", extract={"title": ".title"})

    assert [row["title"] for row in result] == ["Gig 0", "Gig 1", "Gig 2"]


def test_query_all_returns_none_for_a_missing_sub_element():
    card = _StubElement(children={})
    page = _StubPage()
    page.set_query_selector_all(".gig-card", [card])
    session = PlaywrightBrowserSession(page)

    result = session.query_all(".gig-card", extract={"title": ".title"})

    assert result == [{"title": None}]


def test_query_all_bare_attribute_reads_off_the_matched_element_itself():
    card = _StubElement(attributes={"data-id": "42"})
    page = _StubPage()
    page.set_query_selector_all(".gig-card", [card])
    session = PlaywrightBrowserSession(page)

    result = session.query_all(".gig-card", extract={"id": "@data-id"})

    assert result == [{"id": "42"}]
