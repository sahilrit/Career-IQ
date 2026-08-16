from __future__ import annotations

from careeros_job_providers import JobSearchQuery
from careeros_weworkremotely_provider import WeWorkRemotelyProvider, parse_job_entry

ITEM = {
    "title": "Acme Inc: Senior Performance Marketing Manager",
    "description": "<p>Run <b>Meta Ads</b> and scale ROAS.</p>",
    "link": "https://weworkremotely.com/remote-jobs/acme-inc-senior-pmm",
    "region": "Anywhere",
    "category": "Sales and Marketing",
}


def test_parse_splits_company_and_role():
    p = parse_job_entry(ITEM)
    assert p.company_name == "Acme Inc"
    assert p.title == "Senior Performance Marketing Manager"
    assert p.remote is True
    assert "Meta Ads" in p.description


def test_keyword_filter():
    provider = WeWorkRemotelyProvider(type("T", (), {"fetch": lambda self: [ITEM]})())
    assert len(provider.search(JobSearchQuery(keywords=["marketing"])).postings) == 1
    assert provider.search(JobSearchQuery(keywords=["nursing"])).postings == []
