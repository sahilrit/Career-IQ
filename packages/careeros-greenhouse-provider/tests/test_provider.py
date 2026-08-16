"""Tests for Greenhouse parsing and filtering against a fake transport."""

from __future__ import annotations

from careeros_greenhouse_provider import GreenhouseProvider, parse_job_entry
from careeros_job_providers import JobSearchQuery

REMOTE_MARKETING = {
    "id": 1,
    "title": "Performance Marketing Manager, Remote",
    "company_name": "Acme",
    "absolute_url": "https://boards.greenhouse.io/acme/jobs/1",
    "location": {"name": "Remote - US"},
    "content": "<p>Own <strong>Meta Ads</strong> &amp; growth.</p>",
    "updated_at": "2026-08-01T10:00:00-04:00",
}
ONSITE_ENG = {
    "id": 2,
    "title": "Backend Engineer",
    "company_name": "Acme",
    "absolute_url": "https://boards.greenhouse.io/acme/jobs/2",
    "location": {"name": "San Francisco"},
    "content": "<p>Go services.</p>",
}


class FakeTransport:
    def __init__(self, entries):
        self._entries = entries

    def fetch(self):
        return self._entries


def test_parses_and_strips_html_description():
    posting = parse_job_entry(REMOTE_MARKETING)
    assert posting.source_provider == "greenhouse"
    assert posting.remote is True
    assert "Meta Ads" in posting.description
    assert "<" not in posting.description
    assert posting.url == "https://boards.greenhouse.io/acme/jobs/1"


def test_remote_only_query_excludes_onsite():
    provider = GreenhouseProvider(FakeTransport([REMOTE_MARKETING, ONSITE_ENG]))
    result = provider.search(JobSearchQuery(keywords=["marketing"], remote_only=True))
    assert [p.title for p in result.postings] == ["Performance Marketing Manager, Remote"]


def test_keyword_filter_applies():
    provider = GreenhouseProvider(FakeTransport([REMOTE_MARKETING, ONSITE_ENG]))
    result = provider.search(JobSearchQuery(keywords=["backend"], remote_only=False))
    assert [p.title for p in result.postings] == ["Backend Engineer"]


def test_entry_missing_id_or_title_is_skipped():
    provider = GreenhouseProvider(FakeTransport([{"id": 3}, {"title": "x"}]))
    assert provider.search(JobSearchQuery()).postings == []
