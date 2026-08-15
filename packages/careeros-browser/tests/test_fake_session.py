"""Tests for FakeBrowserSession, entirely in-memory — no real browser."""

from __future__ import annotations

from pathlib import Path

import pytest

from careeros_browser import DownloadError, FakeBrowserSession, SelectorTimeoutError


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
