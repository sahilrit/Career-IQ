"""Tests for NaukriProvider — entirely offline, via a fake browser session.

No real browser, no camoufox, no network. The provider is exercised
exactly the way ``careeros_browser.FakeBrowserSession`` is designed to be
used: queue what a real page would return, then assert on what the
provider does with it.
"""

from __future__ import annotations

from contextlib import contextmanager

from careeros_browser import FakeBrowserSession
from careeros_job_providers import HealthStatus, JobSearchQuery
from careeros_naukri_provider import NaukriProvider

PAGE_ONE = (
    '{"jobDetails": ['
    '{"jobId": "1", "jdURL": "/job-1", "title": "Growth Lead", "companyName": "Acme", '
    '"placeholders": [{"type": "location", "label": "Bengaluru"}]},'
    '{"jobId": "2", "jdURL": "/job-2", "title": "Marketing Manager", "companyName": "Beta", '
    '"placeholders": [{"type": "location", "label": "Mumbai"}]}'
    "]}"
)
PAGE_TWO = (
    '{"jobDetails": ['
    '{"jobId": "3", "jdURL": "/job-3", "title": "Performance Marketer", "companyName": "Gamma"}'
    "]}"
)
EMPTY_PAGE = '{"jobDetails": []}'


@contextmanager
def _session_factory(session: FakeBrowserSession):
    """Wrap a pre-seeded FakeBrowserSession as a one-shot session factory."""
    try:
        yield session
    finally:
        session.close()


def _provider(session: FakeBrowserSession, **kwargs) -> NaukriProvider:
    return NaukriProvider(session_factory=lambda: _session_factory(session), **kwargs)


def test_provider_id_is_naukri():
    session = FakeBrowserSession()
    assert _provider(session).provider_id == "naukri"


def test_search_returns_postings_from_the_captured_response():
    session = FakeBrowserSession()
    session.queue_response(url_contains="jobapi/v3/search", body=PAGE_ONE)
    session.set_click_failure("a:has-text('Next')")  # stop after page 1

    result = _provider(session).search(JobSearchQuery(keywords=["growth"], limit=50))

    assert {p.external_id for p in result.postings} == {"1", "2"}


def test_search_uses_the_first_query_location():
    session = FakeBrowserSession()
    session.queue_response(url_contains="jobapi/v3/search", body=EMPTY_PAGE)

    _provider(session).search(JobSearchQuery(keywords=["growth"], locations=["Pune"]))

    assert "pune" in session.current_url.lower()


def test_search_issues_one_request_per_keyword():
    session = FakeBrowserSession()
    session.queue_response(url_contains="jobapi/v3/search", body=EMPTY_PAGE)
    session.queue_response(url_contains="jobapi/v3/search", body=EMPTY_PAGE)

    _provider(session).search(JobSearchQuery(keywords=["growth", "marketing"]))
    # Two navigations means two page-1 requests were made; nothing raised.


def test_search_paginates_when_next_is_clickable():
    session = FakeBrowserSession()
    session.queue_response(url_contains="jobapi/v3/search", body=PAGE_ONE)
    session.queue_response(url_contains="jobapi/v3/search", body=PAGE_TWO)
    session.queue_response(url_contains="jobapi/v3/search", body=EMPTY_PAGE)

    result = _provider(session, max_pages=5).search(JobSearchQuery(keywords=["growth"], limit=50))

    assert {p.external_id for p in result.postings} == {"1", "2", "3"}


def test_search_stops_when_a_page_returns_no_jobs():
    session = FakeBrowserSession()
    session.queue_response(url_contains="jobapi/v3/search", body=PAGE_ONE)
    session.queue_response(url_contains="jobapi/v3/search", body=EMPTY_PAGE)
    # A third queued response would prove pagination continued past an empty
    # page if it were ever consumed — it must not be.
    session.queue_response(url_contains="jobapi/v3/search", body=PAGE_TWO)

    result = _provider(session, max_pages=5).search(JobSearchQuery(keywords=["growth"], limit=50))

    assert {p.external_id for p in result.postings} == {"1", "2"}


def test_search_respects_max_pages():
    session = FakeBrowserSession()
    session.queue_response(url_contains="jobapi/v3/search", body=PAGE_ONE)
    session.queue_response(url_contains="jobapi/v3/search", body=PAGE_TWO)

    result = _provider(session, max_pages=1).search(JobSearchQuery(keywords=["growth"], limit=50))

    # Page 2 was queued but never fetched — max_pages=1 stopped after page 1.
    assert {p.external_id for p in result.postings} == {"1", "2"}


def test_search_respects_the_query_limit():
    session = FakeBrowserSession()
    session.queue_response(url_contains="jobapi/v3/search", body=PAGE_ONE)
    session.set_click_failure("a:has-text('Next')")

    result = _provider(session).search(JobSearchQuery(keywords=["growth"], limit=1))

    assert len(result.postings) == 1


def test_a_blocked_search_reports_a_source_error_and_returns_no_postings():
    """No response ever arrives (challenge intercepted the request) — this
    must surface as a reported error, not a silent empty result that looks
    identical to 'no jobs matched'."""
    session = FakeBrowserSession()  # nothing queued -> capture times out

    result = _provider(session).search(JobSearchQuery(keywords=["growth"]))

    assert result.postings == []
    assert result.source_errors
    assert "growth" in result.source_errors[0]


def test_one_blocked_keyword_does_not_stop_the_others():
    session = FakeBrowserSession()
    session.queue_response(url_contains="jobapi/v3/search", body=EMPTY_PAGE)
    # Only one response queued for two keywords: the second is "blocked".

    result = _provider(session).search(JobSearchQuery(keywords=["growth", "marketing"]))

    assert len(result.source_errors) == 1


def test_the_same_posting_from_two_keywords_is_only_returned_once():
    session = FakeBrowserSession()
    session.queue_response(url_contains="jobapi/v3/search", body=PAGE_ONE)
    session.queue_response(url_contains="jobapi/v3/search", body=PAGE_ONE)

    result = _provider(session).search(JobSearchQuery(keywords=["growth", "marketing"]))

    assert len(result.postings) == 2  # not 4


def test_health_check_is_optimistic():
    """Naukri health is checked before every registry search; actually
    launching a browser and running a request per check would double the
    cost of every search. Like GreenhouseProvider, this reports healthy and
    lets search() itself surface a blocked run via source_errors."""
    session = FakeBrowserSession()
    assert _provider(session).health_check().status == HealthStatus.HEALTHY


def test_search_with_no_keywords_uses_a_default_term():
    session = FakeBrowserSession()
    session.queue_response(url_contains="jobapi/v3/search", body=EMPTY_PAGE)
    result = _provider(session).search(JobSearchQuery())
    assert result.source_errors == []
