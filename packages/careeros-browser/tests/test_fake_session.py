"""Tests for FakeBrowserSession, entirely in-memory — no real browser."""

from __future__ import annotations

from pathlib import Path

import pytest

from careeros_browser import (
    DownloadError,
    FakeBrowserSession,
    ResponseTimeoutError,
    SelectorTimeoutError,
)


def test_goto_updates_current_url():
    session = FakeBrowserSession()
    session.goto("https://example.com")
    assert session.current_url == "https://example.com"


def test_go_back_restores_previous_url():
    session = FakeBrowserSession()
    session.goto("https://example.com/1")
    session.goto("https://example.com/2")
    session.go_back()
    assert session.current_url == "https://example.com/1"


def test_go_back_with_no_history_is_a_no_op():
    session = FakeBrowserSession()
    session.go_back()
    assert session.current_url == "about:blank"


def test_cookies_can_be_set_listed_and_cleared():
    session = FakeBrowserSession()
    session.set_cookie({"name": "session", "value": "abc"})
    assert session.get_cookies() == [{"name": "session", "value": "abc"}]
    session.clear_cookies()
    assert session.get_cookies() == []


def test_fill_records_the_field_value():
    session = FakeBrowserSession()
    session.fill("#email", "ada@example.com")
    assert session.field_value("#email") == "ada@example.com"


def test_click_is_recorded():
    session = FakeBrowserSession()
    session.click("#submit")
    assert session.clicked_selectors == ["#submit"]


def test_upload_file_is_recorded():
    session = FakeBrowserSession()
    session.upload_file("#resume", "/tmp/resume.pdf")
    assert session.uploaded_files["#resume"] == "/tmp/resume.pdf"


def test_set_hidden_undoes_set_visible():
    session = FakeBrowserSession()
    session.set_visible("#captcha")
    session.set_hidden("#captcha")
    assert session.is_visible("#captcha") is False


def test_set_hidden_on_a_never_visible_selector_is_a_no_op():
    session = FakeBrowserSession()
    session.set_hidden("#never-shown")  # must not raise
    assert session.is_visible("#never-shown") is False


def test_wait_for_selector_raises_when_never_made_visible():
    session = FakeBrowserSession()
    with pytest.raises(SelectorTimeoutError):
        session.wait_for_selector("#success-banner", timeout_ms=100)


def test_wait_for_selector_succeeds_once_visible():
    session = FakeBrowserSession()
    session.set_visible("#success-banner", text="Application submitted")
    session.wait_for_selector("#success-banner")
    assert session.is_visible("#success-banner")
    assert session.text_content("#success-banner") == "Application submitted"


def test_download_without_a_queued_download_raises():
    session = FakeBrowserSession()
    with pytest.raises(DownloadError):
        session.download_triggered_by(lambda: None, save_to="/tmp/out.pdf")


def test_download_returns_the_queued_path_after_the_action_runs():
    session = FakeBrowserSession()
    session.queue_download("/tmp/downloaded.pdf")
    calls = []
    result = session.download_triggered_by(lambda: calls.append("clicked"), save_to="/tmp/out.pdf")
    assert calls == ["clicked"]
    assert result == Path("/tmp/downloaded.pdf")


def test_screenshot_is_recorded_and_returns_a_path():
    session = FakeBrowserSession()
    result = session.screenshot("/tmp/shot.png")
    assert result == Path("/tmp/shot.png")
    assert session.screenshots_taken == [Path("/tmp/shot.png")]


def test_close_marks_the_session_closed():
    session = FakeBrowserSession()
    session.close()
    assert session.closed is True


def test_query_all_returns_empty_list_when_nothing_queued():
    session = FakeBrowserSession()
    assert session.query_all(".gig-card", extract={"title": ".title"}) == []


def test_query_all_replays_the_queued_results():
    session = FakeBrowserSession()
    rows = [{"title": "First gig", "url": "https://x.example/1"}]
    session.set_query_all_results(".gig-card", rows)

    result = session.query_all(".gig-card", extract={"title": ".title", "url": "a@href"})

    assert result == rows


def test_query_all_results_are_isolated_by_selector():
    session = FakeBrowserSession()
    session.set_query_all_results(".gig-card", [{"title": "gig"}])
    session.set_query_all_results(".job-card", [{"title": "job"}])

    assert session.query_all(".gig-card", extract={}) == [{"title": "gig"}]
    assert session.query_all(".job-card", extract={}) == [{"title": "job"}]


# --- response capture (regression target: Naukri-style XHR interception) -----


def test_capture_response_after_returns_the_queued_body():
    session = FakeBrowserSession()
    session.queue_response(url_contains="jobapi/v3/search", body='{"jobDetails": []}')
    body = session.capture_response_after(lambda: None, url_contains="jobapi/v3/search")
    assert body == '{"jobDetails": []}'


def test_capture_response_after_runs_the_action():
    session = FakeBrowserSession()
    session.queue_response(url_contains="jobapi", body="{}")
    ran = {"called": False}
    session.capture_response_after(lambda: ran.__setitem__("called", True), url_contains="jobapi")
    assert ran["called"] is True


def test_capture_response_after_matches_by_substring_not_exact_url():
    session = FakeBrowserSession()
    session.queue_response(url_contains="jobapi/v3/search", body='{"page": 1}')
    body = session.capture_response_after(lambda: None, url_contains="jobapi/v3/search")
    assert body == '{"page": 1}'


def test_capture_response_after_with_no_queued_response_raises():
    session = FakeBrowserSession()
    with pytest.raises(ResponseTimeoutError):
        session.capture_response_after(lambda: None, url_contains="jobapi")


def test_capture_response_after_consumes_the_queued_response_once():
    """A second call for the same URL pattern with nothing re-queued must not
    silently replay the first response — pagination depends on each page
    getting its own fresh response."""
    session = FakeBrowserSession()
    session.queue_response(url_contains="jobapi", body="page-one")
    session.capture_response_after(lambda: None, url_contains="jobapi")
    with pytest.raises(ResponseTimeoutError):
        session.capture_response_after(lambda: None, url_contains="jobapi")


def test_capture_response_after_serves_multiple_queued_responses_in_order():
    session = FakeBrowserSession()
    session.queue_response(url_contains="jobapi", body="page-one")
    session.queue_response(url_contains="jobapi", body="page-two")
    first = session.capture_response_after(lambda: None, url_contains="jobapi")
    second = session.capture_response_after(lambda: None, url_contains="jobapi")
    assert (first, second) == ("page-one", "page-two")


# --- outer-HTML extraction (regression target: dt/dd-shaped cards) -----------


def test_query_all_html_returns_empty_list_when_nothing_queued():
    session = FakeBrowserSession()
    assert session.query_all_html("article") == []


def test_query_all_html_replays_the_queued_blocks():
    session = FakeBrowserSession()
    session.set_html_blocks("article", ["<article>one</article>", "<article>two</article>"])
    assert session.query_all_html("article") == [
        "<article>one</article>",
        "<article>two</article>",
    ]


def test_query_all_html_is_isolated_by_selector():
    session = FakeBrowserSession()
    session.set_html_blocks("article", ["<article>a</article>"])
    session.set_html_blocks(".card", ["<div>b</div>"])
    assert session.query_all_html("article") == ["<article>a</article>"]
    assert session.query_all_html(".card") == ["<div>b</div>"]


# --- simulated click failure (regression target: "no more pages" detection) --


def test_click_succeeds_by_default():
    session = FakeBrowserSession()
    session.click("#next")  # must not raise
    assert session.clicked_selectors == ["#next"]


def test_a_selector_marked_to_fail_raises_on_click():
    session = FakeBrowserSession()
    session.set_click_failure("#next")
    with pytest.raises(SelectorTimeoutError):
        session.click("#next")


def test_a_failing_click_is_not_recorded_as_clicked():
    session = FakeBrowserSession()
    session.set_click_failure("#next")
    with pytest.raises(SelectorTimeoutError):
        session.click("#next")
    assert session.clicked_selectors == []


def test_only_the_marked_selector_fails():
    session = FakeBrowserSession()
    session.set_click_failure("#next")
    session.click("#other")  # unaffected
    assert session.clicked_selectors == ["#other"]
