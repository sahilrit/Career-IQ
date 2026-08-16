"""Tests for Himalayas entry parsing."""

from __future__ import annotations

from careeros_himalayas_provider import is_job_entry, parse_job_entry
from careeros_job_providers import EmploymentType

ENTRY = {
    "title": "Performance Marketing Manager",
    "excerpt": "Own paid acquisition.",
    "companyName": "Acme DTC",
    "employmentType": "Full Time",
    "minSalary": 70000,
    "maxSalary": 90000,
    "salaryPeriod": "annual",
    "currency": "USD",
    "locationRestrictions": ["Worldwide"],
    "categories": ["Marketing", "Performance-Marketing"],
    "parentCategories": ["Marketing"],
    "description": "<p>Run Meta ads and scale ROAS.</p>",
    "pubDate": 1786866505,
    "applicationLink": "https://himalayas.app/companies/acme/jobs/pm-manager",
    "guid": "https://himalayas.app/companies/acme/jobs/pm-manager",
}


def test_parses_core_fields():
    posting = parse_job_entry(ENTRY)
    assert posting.source_provider == "himalayas"
    assert posting.title == "Performance Marketing Manager"
    assert posting.company_name == "Acme DTC"
    assert posting.url == "https://himalayas.app/companies/acme/jobs/pm-manager"
    assert posting.remote is True
    assert posting.employment_type == EmploymentType.FULL_TIME
    assert posting.location == "Worldwide"


def test_categories_become_lowercase_tags_without_hyphens():
    posting = parse_job_entry(ENTRY)
    assert "performance marketing" in posting.tags
    assert "marketing" in posting.tags


def test_salary_parsed_with_annual_period():
    posting = parse_job_entry(ENTRY)
    assert posting.salary is not None
    assert posting.salary.min_amount == 70000
    assert posting.salary.period == "year"


def test_hourly_salary_period():
    entry = dict(ENTRY, salaryPeriod="hourly", minSalary=40, maxSalary=60)
    assert parse_job_entry(entry).salary.period == "hour"


def test_missing_salary_is_none():
    entry = {**ENTRY}
    del entry["minSalary"], entry["maxSalary"]
    assert parse_job_entry(entry).salary is None


def test_contractor_maps_to_contract():
    entry = dict(ENTRY, employmentType="Contractor")
    assert parse_job_entry(entry).employment_type == EmploymentType.CONTRACT


def test_posted_at_from_unix_timestamp():
    posting = parse_job_entry(ENTRY)
    assert posting.posted_at is not None
    assert posting.posted_at.year >= 2026


def test_entry_without_title_or_link_is_not_a_job():
    assert not is_job_entry({"title": "", "applicationLink": "x"})
    assert not is_job_entry({"title": "Role"})
    assert is_job_entry({"title": "Role", "applicationLink": "https://x"})


def test_placeholder_company_name_falls_back_to_slug():
    entry = dict(ENTRY, companyName="name", companySlug="the-spark-group")
    assert parse_job_entry(entry).company_name == "The Spark Group"
