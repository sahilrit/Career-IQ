"""Tests for the Golang Jobs provider. No real network calls."""

from __future__ import annotations

from careeros_golangjobs_provider import (
    GolangJobsProvider,
    is_job_entry,
    parse_job_entry,
)
from careeros_job_providers import HealthStatus, JobSearchQuery

# --- parsing -----------------------------------------------------------------


def test_a_row_without_a_title_is_not_usable():
    assert is_job_entry({"id": "1", "company": "x"}) is False


def test_a_row_without_an_id_is_not_usable():
    assert is_job_entry({"title": "Go Dev", "company": "x"}) is False


def test_parse_maps_the_core_fields(rows):
    posting = parse_job_entry(rows[0])
    assert posting.source_provider == "golangjobs"
    assert posting.external_id == "f1410a66-804e-43e5-a3c5-387d2b10d387"
    assert posting.title == "Senior Backend Engineer (Go)"
    assert posting.company_name == "Okta"


def test_parse_prefers_the_direct_application_url(rows):
    assert parse_job_entry(rows[0]).url == "https://okta.example/apply/1"


def test_parse_falls_back_to_the_board_url_when_no_apply_link(rows):
    """The second row has no application_url; the listing page is built from
    the slug so the posting still links somewhere real."""
    posting = parse_job_entry(rows[1])
    assert posting.url.startswith("https://www.golangjobs.tech/")
    assert "go-developer-at-encora" in posting.url


def test_parse_reads_a_salary(rows):
    salary = parse_job_entry(rows[0]).salary
    assert salary is not None
    assert (salary.min_amount, salary.max_amount, salary.currency) == (150000, 190000, "USD")


def test_parse_has_no_salary_when_absent(rows):
    assert parse_job_entry(rows[1]).salary is None


def test_parse_reads_the_posted_date(rows):
    posted = parse_job_entry(rows[0]).posted_at
    assert posted is not None
    assert (posted.year, posted.month, posted.day) == (2026, 8, 20)


def test_remote_is_detected_from_the_text(rows):
    assert parse_job_entry(rows[0]).remote is True  # "Remote within the US"
    assert parse_job_entry(rows[1]).remote is False  # "Onsite in Berlin"


def test_requirements_become_tags(rows):
    assert set(parse_job_entry(rows[0]).tags) >= {"go", "grpc"}


# --- provider ----------------------------------------------------------------


def test_provider_id_is_golangjobs(fake_transport_cls):
    assert GolangJobsProvider(fake_transport_cls()).provider_id == "golangjobs"


def test_search_returns_the_active_rows(fake_transport_cls):
    result = GolangJobsProvider(fake_transport_cls()).search(JobSearchQuery())
    assert {p.external_id for p in result.postings} == {
        "f1410a66-804e-43e5-a3c5-387d2b10d387",
        "a2410a66-804e-43e5-a3c5-387d2b10d999",
    }


def test_search_excludes_archived_rows_server_side(fake_transport_cls):
    transport = fake_transport_cls()
    GolangJobsProvider(transport).search(JobSearchQuery())
    # The archived filter is pushed to the API, not done client-side.
    assert transport.calls[0].get("is_archived") == "eq.false"


def test_search_requests_newest_first(fake_transport_cls):
    transport = fake_transport_cls()
    GolangJobsProvider(transport).search(JobSearchQuery())
    assert "posted_at" in transport.calls[0].get("order", "")


def test_search_applies_the_query_filter_locally(fake_transport_cls):
    """The board is Go-only and small, so keyword narrowing happens locally
    against the fetched rows."""
    result = GolangJobsProvider(fake_transport_cls()).search(JobSearchQuery(keywords=["backend"]))
    assert [p.external_id for p in result.postings] == ["f1410a66-804e-43e5-a3c5-387d2b10d387"]


def test_search_respects_the_limit(fake_transport_cls):
    result = GolangJobsProvider(fake_transport_cls()).search(JobSearchQuery(limit=1))
    assert len(result.postings) == 1


def test_health_check_is_healthy_when_the_api_answers(fake_transport_cls):
    assert GolangJobsProvider(fake_transport_cls()).health_check().status == HealthStatus.HEALTHY


def test_health_check_is_down_when_the_api_fails(fake_transport_cls):
    provider = GolangJobsProvider(fake_transport_cls(raise_error=RuntimeError("503")))
    health = provider.health_check()
    assert health.status == HealthStatus.DOWN
    assert "503" in health.detail
