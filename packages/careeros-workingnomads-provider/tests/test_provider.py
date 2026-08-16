from __future__ import annotations

from careeros_job_providers import JobSearchQuery
from careeros_workingnomads_provider import WorkingNomadsProvider, parse_job_entry

ENTRY = {
    "url": "https://www.workingnomads.com/jobs/acme-ppc",
    "title": "PPC Specialist",
    "description": "<p>Run <b>Google & Meta</b> ads.</p>",
    "company_name": "Acme",
    "category_name": "Marketing",
    "tags": "marketing, ppc, ads",
    "location": "Anywhere",
}


def test_parse_strips_html_and_splits_tags():
    posting = parse_job_entry(ENTRY)
    assert posting.source_provider == "workingnomads"
    assert posting.remote is True
    assert "ppc" in posting.tags and "marketing" in posting.tags
    assert "Google" in posting.description


def test_keyword_filter():
    provider = WorkingNomadsProvider(type("T", (), {"fetch": lambda self: [ENTRY]})())
    assert len(provider.search(JobSearchQuery(keywords=["ppc"])).postings) == 1
    assert provider.search(JobSearchQuery(keywords=["plumbing"])).postings == []
