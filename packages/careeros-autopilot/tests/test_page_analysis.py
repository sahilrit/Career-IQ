"""Tests for live-page form detection and apply-link discovery."""

from __future__ import annotations

from careeros_autopilot import detect_form_mapping, find_apply_url, prepare_application_page
from careeros_browser import FakeBrowserSession
from careeros_job_providers import JobPosting


def make_posting(url="https://example.com/jobs/1") -> JobPosting:
    return JobPosting(
        source_provider="test",
        external_id="1",
        title="Performance Marketing Manager",
        company_name="Acme",
        url=url,
        remote=True,
    )


def test_no_form_and_no_apply_link_returns_reason():
    session = FakeBrowserSession()
    reason = prepare_application_page(session, make_posting())
    assert reason is not None
    assert "no application form" in reason


def test_ats_link_is_preferred_and_navigated_to():
    session = FakeBrowserSession()
    session.set_query_all_results(
        "a",
        [
            {"href": "https://example.com/about"},
            {"href": "https://boards.greenhouse.io/acme/jobs/123"},
        ],
    )
    assert find_apply_url(session) == "https://boards.greenhouse.io/acme/jobs/123"
    assert prepare_application_page(session, make_posting()) is None
    assert session.current_url == "https://boards.greenhouse.io/acme/jobs/123"


def test_generic_apply_suffix_link_is_found():
    session = FakeBrowserSession()
    session.set_query_all_results("a", [{"href": "https://example.com/jobs/1/apply?src=x"}])
    assert find_apply_url(session) == "https://example.com/jobs/1/apply?src=x"


def test_page_that_is_already_a_form_needs_no_navigation():
    session = FakeBrowserSession()
    session.set_visible("input[type='email']")
    session.set_visible("button[type='submit']")
    assert prepare_application_page(session, make_posting()) is None


def test_detect_form_mapping_requires_email_and_submit():
    session = FakeBrowserSession()
    assert detect_form_mapping(session) is None
    session.set_visible("input[type='email']")
    assert detect_form_mapping(session) is None
    session.set_visible("button[type='submit']")
    assert detect_form_mapping(session) is not None


def test_detect_form_mapping_prefers_split_name_fields():
    session = FakeBrowserSession()
    session.set_visible("input[type='email']")
    session.set_visible("button[type='submit']")
    session.set_visible("#first_name")
    session.set_visible("#last_name")
    session.set_visible("input[autocomplete='name']")
    mapping = detect_form_mapping(session)
    assert mapping.first_name_selector == "#first_name"
    assert mapping.last_name_selector == "#last_name"
    assert mapping.full_name_selector is None


def test_detect_form_mapping_picks_up_optional_fields():
    session = FakeBrowserSession()
    for selector in (
        "input[type='email']",
        "button[type='submit']",
        "input[type='tel']",
        "input[type='file']",
        "textarea[name*='cover' i]",
    ):
        session.set_visible(selector)
    mapping = detect_form_mapping(session)
    assert mapping.phone_selector == "input[type='tel']"
    assert mapping.resume_upload_selector == "input[type='file']"
    assert mapping.cover_letter_selector == "textarea[name*='cover' i]"


def test_bot_protection_challenge_is_reported_not_bypassed():
    session = FakeBrowserSession()
    session.set_visible("text=/just a moment/i")
    session.set_query_all_results("a", [{"href": "https://example.com/jobs/1/apply"}])
    reason = prepare_application_page(session, make_posting())
    assert reason is not None
    assert "bot-protection" in reason
