"""Tests for HimalayasProvider against a fake transport."""

from __future__ import annotations

from careeros_himalayas_provider import HimalayasProvider
from careeros_job_providers import JobSearchQuery

MARKETING_ENTRY = {
    "title": "Performance Marketing Manager",
    "companyName": "Acme DTC",
    "employmentType": "Full Time",
    "categories": ["Marketing"],
    "description": "Run Meta ads and scale ROAS for DTC brands.",
    "applicationLink": "https://himalayas.app/companies/acme/jobs/pm",
    "guid": "https://himalayas.app/companies/acme/jobs/pm",
}

ENGINEERING_ENTRY = {
    "title": "Staff Software Engineer",
    "companyName": "TechCo",
    "employmentType": "Full Time",
    "categories": ["Engineering"],
    "description": "Distributed systems in Go.",
    "applicationLink": "https://himalayas.app/companies/techco/jobs/sse",
    "guid": "https://himalayas.app/companies/techco/jobs/sse",
}


class FakeTransport:
    def __init__(self, entries):
        self._entries = entries

    def fetch(self):
        return self._entries


def test_search_filters_by_keywords():
    provider = HimalayasProvider(FakeTransport([MARKETING_ENTRY, ENGINEERING_ENTRY]))
    result = provider.search(JobSearchQuery(keywords=["meta ads"]))
    assert [p.title for p in result.postings] == ["Performance Marketing Manager"]


def test_search_respects_limit():
    provider = HimalayasProvider(FakeTransport([MARKETING_ENTRY, ENGINEERING_ENTRY]))
    result = provider.search(JobSearchQuery(limit=1))
    assert len(result.postings) == 1


def test_provider_id():
    assert HimalayasProvider(FakeTransport([])).provider_id == "himalayas"
