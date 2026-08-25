"""Tests for UkVisaJobsProvider — entirely offline, via a fake browser
session and a fake HTTP transport."""

from __future__ import annotations

import json
from contextlib import contextmanager

from careeros_browser import FakeBrowserSession
from careeros_job_providers import HealthStatus, JobSearchQuery
from careeros_ukvisajobs_provider.parser import OPEN_JOBS_URL
from careeros_ukvisajobs_provider.provider import UkVisaJobsProvider


class FakeTransport:
    """Records every fetch and replays queued (status_code, body) pairs."""

    def __init__(self) -> None:
        self._pages: list[tuple[int, str]] = []
        self.calls: list[dict] = []

    def queue_page(self, *, status_code: int = 200, body: str) -> None:
        self._pages.append((status_code, body))

    def fetch_page(self, *, page_no, search_keyword, session):
        self.calls.append(
            {
                "page_no": page_no,
                "search_keyword": search_keyword,
                "token": session.token,
            }
        )
        if not self._pages:
            return (200, '{"status": 1, "totalJobs": 0, "jobs": []}')
        return self._pages.pop(0)


def _page_body(jobs: list[dict], *, total: int | None = None) -> str:
    return json.dumps({"status": 1, "totalJobs": total or len(jobs), "jobs": jobs})


def _job(job_id: str) -> dict:
    return {
        "id": job_id,
        "title": f"Role {job_id}",
        "company_name": "Acme UK",
        "job_link": f"https://my.ukvisajobs.com/job/{job_id}",
    }


@contextmanager
def _session_factory(session: FakeBrowserSession):
    try:
        yield session
    finally:
        session.close()


def _logged_in_session() -> FakeBrowserSession:
    session = FakeBrowserSession()
    session.set_visible("#email")
    session.set_cookie({"name": "authToken", "value": "auth-tok"})
    session.set_cookie({"name": "csrf_token", "value": "csrf-tok"})
    session.set_cookie({"name": "ci_session", "value": "ci-tok"})
    return session


def _provider(session, transport, **kwargs) -> UkVisaJobsProvider:
    return UkVisaJobsProvider(
        session_factory=lambda: _session_factory(session),
        transport=transport,
        credentials=("user@example.com", "hunter2"),
        **kwargs,
    )


def test_provider_id_is_ukvisajobs():
    session = _logged_in_session()
    assert _provider(session, FakeTransport()).provider_id == "ukvisajobs"


def test_search_without_credentials_returns_empty_and_reports_why():
    session = _logged_in_session()
    provider = UkVisaJobsProvider(
        session_factory=lambda: _session_factory(session),
        transport=FakeTransport(),
        credentials=None,
    )
    result = provider.search(JobSearchQuery(limit=10))
    assert result.postings == []
    assert result.source_errors


def test_a_successful_login_ends_up_on_the_open_jobs_page():
    session = _logged_in_session()
    transport = FakeTransport()
    transport.queue_page(body=_page_body([_job("1")]))
    _provider(session, transport).search(JobSearchQuery(limit=10))
    assert session.current_url == OPEN_JOBS_URL


def test_login_fills_credentials_and_submits_with_enter():
    session = _logged_in_session()
    transport = FakeTransport()
    transport.queue_page(body=_page_body([_job("1")]))
    _provider(session, transport).search(JobSearchQuery(limit=10))
    assert session.field_value("#email") == "user@example.com"
    assert session.field_value("#password") == "hunter2"
    assert ("#password", "Enter") in session.pressed_keys


def test_login_failure_when_the_email_field_never_appears():
    session = FakeBrowserSession()  # #email never made visible
    transport = FakeTransport()
    result = _provider(session, transport).search(JobSearchQuery(limit=10))
    assert result.postings == []
    assert result.source_errors
    assert transport.calls == []  # never got as far as fetching a page


def test_login_failure_when_no_authtoken_cookie_is_set():
    session = FakeBrowserSession()
    session.set_visible("#email")  # form appears, but login doesn't actually work
    transport = FakeTransport()
    result = _provider(session, transport).search(JobSearchQuery(limit=10))
    assert result.postings == []
    assert result.source_errors


def test_a_successful_search_maps_postings():
    session = _logged_in_session()
    transport = FakeTransport()
    transport.queue_page(body=_page_body([_job("1"), _job("2")]))

    result = _provider(session, transport).search(JobSearchQuery(limit=10))

    assert {p.external_id for p in result.postings} == {"1", "2"}
    assert result.postings[0].source_provider == "ukvisajobs"


def test_the_captured_auth_token_is_used_as_the_api_token():
    session = _logged_in_session()
    transport = FakeTransport()
    transport.queue_page(body=_page_body([_job("1")]))
    _provider(session, transport).search(JobSearchQuery(limit=10))
    assert transport.calls[0]["token"] == "auth-tok"


def test_pagination_stops_once_a_page_returns_fewer_than_a_full_page():
    session = _logged_in_session()
    transport = FakeTransport()
    full_page = [_job(str(i)) for i in range(15)]
    transport.queue_page(body=_page_body(full_page))
    transport.queue_page(body=_page_body([_job("last")]))

    result = _provider(session, transport).search(JobSearchQuery(limit=100))

    assert len(result.postings) == 16
    assert len(transport.calls) == 2  # did not fetch a third page


def test_pagination_stops_at_max_pages():
    session = _logged_in_session()
    transport = FakeTransport()
    for page in range(5):
        transport.queue_page(body=_page_body([_job(f"{page}-{i}") for i in range(15)]))

    result = _provider(session, transport, max_pages=2).search(JobSearchQuery(limit=1000))

    assert len(transport.calls) == 2
    assert len(result.postings) == 30


def test_search_stops_once_the_limit_is_reached():
    session = _logged_in_session()
    transport = FakeTransport()
    transport.queue_page(body=_page_body([_job(str(i)) for i in range(15)]))
    transport.queue_page(body=_page_body([_job(str(i)) for i in range(15, 30)]))

    result = _provider(session, transport).search(JobSearchQuery(limit=5))

    assert len(result.postings) == 5


def test_an_auth_error_mid_pagination_stops_and_is_reported():
    session = _logged_in_session()
    transport = FakeTransport()
    transport.queue_page(body=_page_body([_job(str(i)) for i in range(15)]))
    transport.queue_page(status_code=401, body="")

    result = _provider(session, transport).search(JobSearchQuery(limit=100))

    assert len(result.postings) == 15
    assert result.source_errors


def test_search_uses_query_keywords_as_search_terms():
    session = _logged_in_session()
    transport = FakeTransport()
    transport.queue_page(body=_page_body([_job("1")]))
    transport.queue_page(body=_page_body([_job("2")]))

    _provider(session, transport).search(
        JobSearchQuery(keywords=["graduate", "engineer"], limit=100)
    )

    assert [call["search_keyword"] for call in transport.calls] == ["graduate", "engineer"]


def test_no_keywords_searches_once_with_no_keyword():
    session = _logged_in_session()
    transport = FakeTransport()
    transport.queue_page(body=_page_body([_job("1")]))
    _provider(session, transport).search(JobSearchQuery(limit=10))
    assert transport.calls[0]["search_keyword"] is None


def test_the_same_posting_across_search_terms_is_only_returned_once():
    session = _logged_in_session()
    transport = FakeTransport()
    transport.queue_page(body=_page_body([_job("1")]))
    transport.queue_page(body=_page_body([_job("1")]))

    result = _provider(session, transport).search(
        JobSearchQuery(keywords=["graduate", "engineer"], limit=100)
    )

    assert len(result.postings) == 1


def test_health_check_is_optimistic():
    session = _logged_in_session()
    assert _provider(session, FakeTransport()).health_check().status == HealthStatus.HEALTHY
