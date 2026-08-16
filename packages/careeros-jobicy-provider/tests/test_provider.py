from __future__ import annotations

from careeros_job_providers import JobSearchQuery
from careeros_jobicy_provider import JobicyProvider, parse_job_entry

ENTRY = {
    "id": 1,
    "jobTitle": "Growth Marketing Manager",
    "companyName": "Acme",
    "url": "https://jobicy.com/jobs/acme-growth",
    "jobGeo": "Anywhere",
    "jobType": ["full-time"],
    "jobIndustry": ["Marketing"],
    "jobDescription": "<p>Own <b>paid</b> growth.</p>",
    "jobExcerpt": "Growth role",
}


def test_parse_strips_html_and_marks_remote():
    posting = parse_job_entry(ENTRY)
    assert posting.source_provider == "jobicy"
    assert posting.remote is True
    assert "paid" in posting.description
    assert "marketing" in posting.tags


def test_keyword_filter():
    provider = JobicyProvider(type("T", (), {"fetch": lambda self: [ENTRY]})())
    assert len(provider.search(JobSearchQuery(keywords=["growth"])).postings) == 1
    assert provider.search(JobSearchQuery(keywords=["welding"])).postings == []
