"""Tests for SeekProvider. No real network calls."""

from __future__ import annotations

import json

from careeros_job_providers import HealthStatus, JobSearchQuery
from careeros_seek_provider import SeekProvider


class FakeTransport:
    def __init__(self) -> None:
        self._pages: list[str] = []
        self.calls: list[dict] = []

    def queue_page(self, jobs: list[dict], *, total_count: int | None = None) -> None:
        self._pages.append(json.dumps({"totalCount": total_count or len(jobs), "data": jobs}))

    def search(self, *, keywords: str, location: str | None, page: int) -> str:
        self.calls.append({"keywords": keywords, "location": location, "page": page})
        if not self._pages:
            return '{"totalCount": 0, "data": []}'
        return self._pages.pop(0)


def _job(job_id: str) -> dict:
    return {"id": job_id, "title": f"Role {job_id}", "companyName": "Acme"}


def test_provider_id_is_seek():
    assert SeekProvider(FakeTransport()).provider_id == "seek"


def test_search_returns_the_usable_results():
    transport = FakeTransport()
    transport.queue_page([_job("1"), _job("2")])
    result = SeekProvider(transport).search(JobSearchQuery(limit=10))
    assert {p.external_id for p in result.postings} == {"1", "2"}


def test_search_joins_keywords_with_a_space():
    transport = FakeTransport()
    transport.queue_page([_job("1")])
    SeekProvider(transport).search(JobSearchQuery(keywords=["growth", "marketing"], limit=10))
    assert transport.calls[0]["keywords"] == "growth marketing"


def test_search_passes_the_first_location():
    transport = FakeTransport()
    transport.queue_page([_job("1")])
    SeekProvider(transport).search(JobSearchQuery(locations=["Sydney"], limit=10))
    assert transport.calls[0]["location"] == "Sydney"


def test_search_stops_once_a_page_returns_fewer_than_a_full_page():
    transport = FakeTransport()
    transport.queue_page([_job(str(i)) for i in range(20)])
    transport.queue_page([_job("last")])
    result = SeekProvider(transport).search(JobSearchQuery(limit=100))
    assert len(result.postings) == 21
    assert len(transport.calls) == 2


def test_search_stops_at_max_pages():
    transport = FakeTransport()
    for page in range(5):
        transport.queue_page([_job(f"{page}-{i}") for i in range(20)])
    result = SeekProvider(transport, max_pages=2).search(JobSearchQuery(limit=1000))
    assert len(transport.calls) == 2
    assert len(result.postings) == 40


def test_search_respects_the_limit():
    transport = FakeTransport()
    transport.queue_page([_job(str(i)) for i in range(20)])
    result = SeekProvider(transport).search(JobSearchQuery(limit=5))
    assert len(result.postings) == 5


def test_search_stops_when_a_page_comes_back_empty():
    transport = FakeTransport()
    transport.queue_page([])
    result = SeekProvider(transport).search(JobSearchQuery(limit=100))
    assert result.postings == []
    assert len(transport.calls) == 1


def test_search_deduplicates_across_pages():
    transport = FakeTransport()
    transport.queue_page([_job(str(i)) for i in range(20)])
    transport.queue_page([_job("0")])  # same id repeated
    result = SeekProvider(transport).search(JobSearchQuery(limit=100))
    assert len(result.postings) == 20


def test_health_check_is_optimistic():
    assert SeekProvider(FakeTransport()).health_check().status == HealthStatus.HEALTHY
