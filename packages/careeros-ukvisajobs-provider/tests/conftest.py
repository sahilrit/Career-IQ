"""Shared fixtures for UK Visa Jobs provider tests. No real network or browser.

Row shapes mirror ``ukvisa-api/api/fetch-jobs-data``'s real response fields
(``company_name``, ``job_link``, ``min_salary``/``max_salary``,
``visa_acceptance``, ...) — this is a credentialed-login API with no public
docs, so field names come from the request/response contract observed by a
working integration, not guessed.
"""

from __future__ import annotations

from typing import Any

import pytest

ROW_FULL: dict[str, Any] = {
    "id": "88123",
    "title": "Graduate Software Engineer",
    "company_name": "Acme UK Ltd",
    "company_link": "https://my.ukvisajobs.com/company/acme-uk",
    "job_link": "https://my.ukvisajobs.com/job/graduate-software-engineer-88123",
    "city": "London",
    "created_date": "2026-08-01",
    "job_expire": "2026-09-30",
    "description": "Join our platform team building the next generation of visa-sponsored tooling.",
    "min_salary": "32000",
    "max_salary": "38000",
    "salary_interval": "year",
    "degree_requirement": "Bachelor's degree",
    "job_type": "Full-time",
    "job_level": "Graduate",
    "job_industry": "Software Engineering",
    "visa_acceptance": "Yes",
    "applicants_outside_uk": "No",
    "likely_to_sponsor": "Yes",
    "definitely_sponsored": "No",
    "new_entrant": "Yes",
    "student_graduate": "Yes",
}

ROW_MINIMAL: dict[str, Any] = {
    "id": "88999",
    "title": "Remote Data Analyst",
    "company_name": "Widget Co",
    "job_link": "https://my.ukvisajobs.com/job/remote-data-analyst-88999",
    "city": "Remote",
}

ROW_UNUSABLE: dict[str, Any] = {"id": "1", "title": "No job_link at all"}

SEARCH_RESPONSE_BODY = (
    '{"status": 1, "totalJobs": 2, "jobs": ['
    '{"id": "1", "title": "A", "company_name": "X", "job_link": "https://my.ukvisajobs.com/job/1"},'
    '{"id": "2", "title": "B", "company_name": "Y", "job_link": "https://my.ukvisajobs.com/job/2"}'
    "]}"
)


@pytest.fixture
def row_full() -> dict[str, Any]:
    return ROW_FULL


@pytest.fixture
def row_minimal() -> dict[str, Any]:
    return ROW_MINIMAL


@pytest.fixture
def row_unusable() -> dict[str, Any]:
    return ROW_UNUSABLE


@pytest.fixture
def search_response_body() -> str:
    return SEARCH_RESPONSE_BODY
