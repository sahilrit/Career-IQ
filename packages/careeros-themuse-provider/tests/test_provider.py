from __future__ import annotations

from careeros_job_providers import JobSearchQuery
from careeros_themuse_provider import TheMuseProvider, parse_job_entry

REMOTE = {
    "id": 1,
    "name": "Performance Marketing Manager",
    "company": {"name": "Acme"},
    "locations": [{"name": "Flexible / Remote"}],
    "categories": [{"name": "Marketing"}],
    "levels": [{"name": "Mid Level"}],
    "contents": "<p>Own <b>paid</b> growth.</p>",
    "refs": {"landing_page": "https://www.themuse.com/jobs/acme/pmm"},
}
ONSITE = {
    "id": 2,
    "name": "Office Manager",
    "company": {"name": "Acme"},
    "locations": [{"name": "New York, NY"}],
    "categories": [{"name": "Administration"}],
    "contents": "Front desk.",
    "refs": {"landing_page": "https://www.themuse.com/jobs/acme/om"},
}


class FakeTransport:
    def __init__(self, entries):
        self._entries = entries

    def fetch(self):
        return self._entries


def test_parse_flags_remote_and_strips_html():
    p = parse_job_entry(REMOTE)
    assert p.source_provider == "themuse"
    assert p.remote is True
    assert "paid" in p.description
    assert p.url == "https://www.themuse.com/jobs/acme/pmm"


def test_remote_only_excludes_onsite():
    provider = TheMuseProvider(FakeTransport([REMOTE, ONSITE]))
    result = provider.search(JobSearchQuery(keywords=["marketing"], remote_only=True))
    assert [p.title for p in result.postings] == ["Performance Marketing Manager"]
