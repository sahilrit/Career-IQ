"""Tests for GlassdoorProvider — entirely offline, via a fake browser
session that queues page state per navigation."""

from __future__ import annotations

from collections import deque
from contextlib import contextmanager

from careeros_browser import FakeBrowserSession
from careeros_glassdoor_provider.parser import CARD_SELECTOR
from careeros_glassdoor_provider.provider import GlassdoorProvider
from careeros_job_providers import HealthStatus, JobSearchQuery

_LISTING_MARKER = '{"@type":"ItemList"}'


class QueuedPageSession(FakeBrowserSession):
    """Each ``goto`` pops the next queued (body_marker_html, cards) pair,
    served on the following ``query_all_html`` calls — mirrors the real
    session's per-page body + card-selector reads."""

    def __init__(self) -> None:
        super().__init__()
        self._pages: deque[tuple[str, list[str]]] = deque()
        self._current_body = "<html></html>"
        self._current_cards: list[str] = []

    def queue_page(self, cards: list[str], *, blocked: bool = False) -> None:
        body = "<html></html>" if blocked else f"<html>{_LISTING_MARKER}</html>"
        self._pages.append((body, cards))

    def goto(self, url: str) -> None:
        super().goto(url)
        self._current_body, self._current_cards = (
            self._pages.popleft() if self._pages else ("<html></html>", [])
        )

    def query_all_html(self, selector: str) -> list[str]:
        if selector == CARD_SELECTOR:
            return list(self._current_cards)
        return [self._current_body]


def _card(job_id: str) -> str:
    return (
        f'<div data-test="job-card-wrapper">'
        f'<span class="EmployerProfile_compactEmployerName__x">Acme</span>'
        f'<a data-test="job-title" href="https://www.glassdoor.com/x.htm?jl={job_id}" '
        f'id="job-title-{job_id}">Role {job_id}</a>'
        f"</div>"
    )


@contextmanager
def _session_factory(session: FakeBrowserSession):
    try:
        yield session
    finally:
        session.close()


def _provider(session: FakeBrowserSession, **kwargs) -> GlassdoorProvider:
    return GlassdoorProvider(session_factory=lambda: _session_factory(session), **kwargs)


def test_provider_id_is_glassdoor():
    assert _provider(QueuedPageSession()).provider_id == "glassdoor"


def test_search_returns_the_usable_postings():
    session = QueuedPageSession()
    session.queue_page([_card("1"), _card("2")])
    result = _provider(session).search(JobSearchQuery(limit=10))
    assert {p.external_id for p in result.postings} == {"1", "2"}


def test_search_stops_once_a_page_returns_fewer_than_a_full_page():
    session = QueuedPageSession()
    session.queue_page([_card(str(i)) for i in range(30)])
    session.queue_page([_card("999")])
    result = _provider(session).search(JobSearchQuery(limit=100))
    assert len(result.postings) == 31


def test_search_stops_at_max_pages():
    session = QueuedPageSession()
    for page in range(5):
        session.queue_page([_card(str(page * 100 + i)) for i in range(30)])
    result = _provider(session, max_pages=2).search(JobSearchQuery(limit=1000))
    assert len(result.postings) == 60


def test_search_respects_the_limit():
    session = QueuedPageSession()
    session.queue_page([_card(str(i)) for i in range(30)])
    result = _provider(session).search(JobSearchQuery(limit=5))
    assert len(result.postings) == 5


def test_a_blocked_page_is_reported_not_silently_empty():
    session = QueuedPageSession()
    session.queue_page([], blocked=True)
    result = _provider(session).search(JobSearchQuery(keywords=["x"], limit=10))
    assert result.postings == []
    assert result.source_errors


def test_a_genuinely_empty_result_page_is_not_reported_as_an_error():
    session = QueuedPageSession()
    session.queue_page([])  # real page, just no cards
    result = _provider(session).search(JobSearchQuery(limit=10))
    assert result.postings == []
    assert result.source_errors == []


def test_search_uses_query_keywords():
    session = QueuedPageSession()
    session.queue_page([_card("1")])
    _provider(session).search(JobSearchQuery(keywords=["growth marketing"], limit=10))
    assert "growth+marketing" in session.current_url


def test_the_same_posting_across_pages_is_only_returned_once():
    session = QueuedPageSession()
    session.queue_page([_card("1")] * 30)
    result = _provider(session).search(JobSearchQuery(limit=100))
    assert len(result.postings) == 1


def test_health_check_is_optimistic():
    assert _provider(QueuedPageSession()).health_check().status == HealthStatus.HEALTHY
