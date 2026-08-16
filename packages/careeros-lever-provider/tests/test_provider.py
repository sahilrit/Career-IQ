from __future__ import annotations

from careeros_job_providers import JobSearchQuery
from careeros_lever_provider import LeverProvider, is_job_entry, parse_job_entry

REMOTE = {
    "id": "1",
    "text": "Growth Marketing Manager",
    "categories": {"commitment": "Full-time", "location": "Remote - US", "department": "Marketing"},
    "workplaceType": "remote",
    "descriptionPlain": "Own paid acquisition.",
    "hostedUrl": "https://jobs.lever.co/acme/1",
    "applyUrl": "https://jobs.lever.co/acme/1/apply",
    "_company": "acme",
}
ONSITE = {
    "id": "2",
    "text": "Backend Engineer",
    "categories": {"commitment": "Full-time", "location": "London", "department": "Eng"},
    "workplaceType": "hybrid",
    "descriptionPlain": "Go.",
    "applyUrl": "https://jobs.lever.co/acme/2/apply",
}


class FakeTransport:
    def __init__(self, entries):
        self._entries = entries

    def fetch(self):
        return self._entries


def test_parse_uses_apply_url_and_remote_flag():
    p = parse_job_entry(REMOTE)
    assert p.source_provider == "lever"
    assert p.remote is True
    assert p.url == "https://jobs.lever.co/acme/1/apply"
    assert "marketing" in p.tags


def test_remote_only_excludes_onsite():
    provider = LeverProvider(FakeTransport([REMOTE, ONSITE]))
    result = provider.search(JobSearchQuery(keywords=["marketing"], remote_only=True))
    assert [p.title for p in result.postings] == ["Growth Marketing Manager"]


def test_is_job_entry_requires_url():
    assert not is_job_entry({"text": "x"})
    assert is_job_entry({"text": "x", "applyUrl": "https://jobs.lever.co/a/b/apply"})
