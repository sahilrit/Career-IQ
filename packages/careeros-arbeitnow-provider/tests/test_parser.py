"""Tests for Arbeitnow JSON entry parsing."""

from __future__ import annotations

from careeros_arbeitnow_provider.parser import parse_job_entry
from careeros_job_providers import EmploymentType


def test_parses_core_fields(arbeitnow_fixture):
    posting = parse_job_entry(arbeitnow_fixture[0])
    assert posting.source_provider == "arbeitnow"
    assert posting.external_id == "senior-backend-engineer-acme"
    assert posting.title == "Senior Backend Engineer"
    assert posting.company_name == "Acme Corp"
    assert posting.url == "https://www.arbeitnow.com/jobs/senior-backend-engineer-acme"
    assert posting.tags == ["python", "django", "postgres"]


def test_remote_flag_is_read_from_the_entry(arbeitnow_fixture):
    assert parse_job_entry(arbeitnow_fixture[0]).remote is True
    assert parse_job_entry(arbeitnow_fixture[1]).remote is False


def test_job_type_is_mapped_to_employment_type(arbeitnow_fixture):
    assert parse_job_entry(arbeitnow_fixture[0]).employment_type == EmploymentType.FULL_TIME
    assert parse_job_entry(arbeitnow_fixture[1]).employment_type == EmploymentType.CONTRACT


def test_unknown_job_type_yields_no_employment_type():
    posting = parse_job_entry(
        {"slug": "x", "title": "Engineer", "company_name": "Acme", "job_types": ["Volunteer"]}
    )
    assert posting.employment_type is None


def test_no_job_types_yields_no_employment_type():
    posting = parse_job_entry({"slug": "x", "title": "Engineer", "company_name": "Acme"})
    assert posting.employment_type is None


def test_parses_posted_at_from_unix_timestamp(arbeitnow_fixture):
    posting = parse_job_entry(arbeitnow_fixture[0])
    assert posting.posted_at is not None
    assert posting.posted_at.year == 2026


def test_missing_created_at_yields_no_posted_at():
    posting = parse_job_entry({"slug": "x", "title": "Engineer", "company_name": "Acme"})
    assert posting.posted_at is None


def test_invalid_created_at_yields_no_posted_at():
    posting = parse_job_entry(
        {"slug": "x", "title": "Engineer", "company_name": "Acme", "created_at": "not-a-number"}
    )
    assert posting.posted_at is None


def test_salary_is_always_none():
    """Arbeitnow's public feed doesn't expose salary data."""
    posting = parse_job_entry({"slug": "x", "title": "Engineer", "company_name": "Acme"})
    assert posting.salary is None
