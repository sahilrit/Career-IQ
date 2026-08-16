from __future__ import annotations

from careeros_ashby_provider import AshbyProvider, is_job_entry, parse_job_entry
from careeros_job_providers import JobSearchQuery

REMOTE_MARKETING = {
    "id": "abc",
    "title": "Growth Marketing Lead",
    "department": "Marketing",
    "team": "Growth",
    "employmentType": "FullTime",
    "location": "Remote - US",
    "isRemote": True,
    "descriptionPlain": "Own paid acquisition and Meta Ads.",
    "applyUrl": "https://jobs.ashbyhq.com/acme/abc",
    "jobUrl": "https://jobs.ashbyhq.com/acme/abc",
    "_company": "acme",
}
ONSITE_ENG = {
    "id": "def",
    "title": "Backend Engineer",
    "employmentType": "FullTime",
    "location": "NYC",
    "isRemote": False,
    "descriptionPlain": "Go services.",
    "applyUrl": "https://jobs.ashbyhq.com/acme/def",
}


class FakeTransport:
    def __init__(self, entries):
        self._entries = entries

    def fetch(self):
        return self._entries


def test_parse_uses_apply_url_and_isremote():
    posting = parse_job_entry(REMOTE_MARKETING)
    assert posting.source_provider == "ashby"
    assert posting.remote is True
    assert posting.url == "https://jobs.ashbyhq.com/acme/abc"
    assert "marketing" in posting.tags
    assert "Meta Ads" in posting.description


def test_remote_only_excludes_onsite():
    provider = AshbyProvider(FakeTransport([REMOTE_MARKETING, ONSITE_ENG]))
    result = provider.search(JobSearchQuery(keywords=["marketing"], remote_only=True))
    assert [p.title for p in result.postings] == ["Growth Marketing Lead"]


def test_entry_without_url_is_not_a_job():
    assert not is_job_entry({"title": "x"})
    assert is_job_entry({"title": "x", "applyUrl": "https://jobs.ashbyhq.com/a/b"})
