"""Tests for ZipRecruiterProvider — entirely offline, via a fake browser
session that queues page HTML per navigation."""

from __future__ import annotations

import json
from collections import deque
from contextlib import contextmanager

from careeros_browser import FakeBrowserSession
from careeros_job_providers import HealthStatus, JobSearchQuery
from careeros_ziprecruiter_provider.provider import ZipRecruiterProvider


class QueuedHtmlSession(FakeBrowserSession):
    """Returns the next queued page body each time the body HTML is read,
    regardless of the URL navigated to — mirrors the real session's
    single ``query_all_html('body')`` call per page fetch."""

    def __init__(self) -> None:
        super().__init__()
        self._pages: deque[str] = deque()

    def queue_page(self, html: str) -> None:
        self._pages.append(html)

    def query_all_html(self, selector: str) -> list[str]:
        if not self._pages:
            return ["<html><body></body></html>"]
        return [self._pages.popleft()]


def _listing_html(items: list[dict]) -> str:
    payload = {"@type": "ItemList", "numberOfItems": len(items), "itemListElement": items}
    script = f'<script type="application/ld+json">{json.dumps(payload)}</script>'
    return f"<html><body>{script}</body></html>"


def _item(jid: str) -> dict:
    return {
        "name": f"Role {jid}",
        "url": f"https://www.ziprecruiter.com/c/Acme/Job/X/-in-Austin,TX?jid={jid}",
    }


@contextmanager
def _session_factory(session: FakeBrowserSession):
    try:
        yield session
    finally:
        session.close()


def _provider(session: FakeBrowserSession, **kwargs) -> ZipRecruiterProvider:
    return ZipRecruiterProvider(session_factory=lambda: _session_factory(session), **kwargs)


def test_provider_id_is_ziprecruiter():
    session = QueuedHtmlSession()
    assert _provider(session).provider_id == "ziprecruiter"


def test_search_returns_the_usable_postings():
    session = QueuedHtmlSession()
    session.queue_page(_listing_html([_item("1"), _item("2")]))
    result = _provider(session).search(JobSearchQuery(limit=10))
    assert {p.external_id for p in result.postings} == {"1", "2"}


def test_search_stops_once_a_page_returns_fewer_than_a_full_page():
    session = QueuedHtmlSession()
    session.queue_page(_listing_html([_item(str(i)) for i in range(20)]))
    session.queue_page(_listing_html([_item("last")]))
    result = _provider(session).search(JobSearchQuery(limit=100))
    assert len(result.postings) == 21


def test_search_stops_at_max_pages():
    session = QueuedHtmlSession()
    for page in range(5):
        session.queue_page(_listing_html([_item(f"{page}-{i}") for i in range(20)]))
    result = _provider(session, max_pages=2).search(JobSearchQuery(limit=1000))
    assert len(result.postings) == 40


def test_search_respects_the_limit():
    session = QueuedHtmlSession()
    session.queue_page(_listing_html([_item(str(i)) for i in range(20)]))
    result = _provider(session).search(JobSearchQuery(limit=5))
    assert len(result.postings) == 5


def test_search_stops_when_a_page_has_no_items():
    session = QueuedHtmlSession()
    session.queue_page(_listing_html([]))
    result = _provider(session).search(JobSearchQuery(limit=100))
    assert result.postings == []


def test_a_challenge_page_with_no_json_ld_is_reported_not_silently_empty():
    """A page that never resolved the Cloudflare challenge has no
    itemListElement at all — that must be distinguishable from 'this
    search genuinely has zero results'."""
    session = QueuedHtmlSession()
    session.queue_page("<html><body>Just a moment...</body></html>")
    result = _provider(session).search(JobSearchQuery(keywords=["x"], limit=10))
    assert result.postings == []
    assert result.source_errors


def test_a_genuinely_empty_result_page_is_not_reported_as_an_error():
    session = QueuedHtmlSession()
    session.queue_page(_listing_html([]))
    result = _provider(session).search(JobSearchQuery(limit=10))
    assert result.source_errors == []


def test_search_uses_query_keywords():
    session = QueuedHtmlSession()
    session.queue_page(_listing_html([_item("1")]))
    _provider(session).search(JobSearchQuery(keywords=["growth marketing"], limit=10))
    assert "growth+marketing" in session.current_url


def test_search_uses_the_first_location():
    session = QueuedHtmlSession()
    session.queue_page(_listing_html([_item("1")]))
    _provider(session).search(JobSearchQuery(locations=["Austin, TX"], limit=10))
    assert "Austin" in session.current_url


def test_the_same_posting_across_pages_is_only_returned_once():
    session = QueuedHtmlSession()
    session.queue_page(_listing_html([_item("1")] * 20))
    result = _provider(session).search(JobSearchQuery(limit=100))
    assert len(result.postings) == 1


def test_health_check_is_optimistic():
    session = QueuedHtmlSession()
    assert _provider(session).health_check().status == HealthStatus.HEALTHY
