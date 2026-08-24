"""Tests for WorkingNomadsProvider against the search backend.

The provider used to read the thin ``/api/exposed_jobs/`` feed, which has
no salary, no publish date and no relevance ranking. It now queries the
same search backend the site's own job search uses.
"""

from __future__ import annotations

from careeros_job_providers import EmploymentType, HealthStatus, JobSearchQuery
from careeros_workingnomads_provider import WorkingNomadsProvider, parse_job_entry


def test_parse_strips_html_and_keeps_tags(search_docs):
    posting = parse_job_entry(search_docs[0])
    assert posting.source_provider == "workingnomads"
    assert posting.remote is True
    assert "seo" in posting.tags
    # Category is folded into tags so keyword matching can use it.
    assert "marketing" in posting.tags
    assert "PPC" in posting.description
    assert "<" not in posting.description
    # &nbsp; must collapse to a real space, not stay glued to the next word.
    assert "ASSOCIATE (Entry-Level)" in posting.description


def test_parse_reads_the_publish_date(search_docs):
    posting = parse_job_entry(search_docs[0])
    assert posting.posted_at is not None
    assert (posting.posted_at.year, posting.posted_at.month) == (2026, 7)


def test_parse_reads_the_salary(search_docs):
    salary = parse_job_entry(search_docs[0]).salary
    assert salary is not None
    assert salary.max_amount == 65000
    assert salary.currency == "USD"


def test_parse_leaves_salary_unset_when_the_feed_has_none(search_docs):
    assert parse_job_entry(search_docs[1]).salary is None


def test_parse_maps_the_employment_type(search_docs):
    assert parse_job_entry(search_docs[0]).employment_type is EmploymentType.FULL_TIME
    assert parse_job_entry(search_docs[1]).employment_type is EmploymentType.CONTRACT


def test_parse_builds_the_public_job_url(search_docs):
    posting = parse_job_entry(search_docs[0])
    assert posting.url == (
        "https://www.workingnomads.com/jobs/marketing-associate-reflex-media-inc-1752874"
    )


def test_parse_uses_the_stable_numeric_id(search_docs):
    assert parse_job_entry(search_docs[0]).external_id == "1752874"


def test_search_sends_the_keywords_to_the_backend(fake_transport_cls):
    transport = fake_transport_cls()
    WorkingNomadsProvider(transport).search(JobSearchQuery(keywords=["ppc", "growth"]))
    assert transport.search_calls[0]["keywords"] == ["ppc", "growth"]


def test_search_drops_expired_postings(fake_transport_cls):
    provider = WorkingNomadsProvider(fake_transport_cls())
    result = provider.search(JobSearchQuery())
    assert "1700000" not in {p.external_id for p in result.postings}


def test_search_does_not_refilter_keywords_the_backend_matched(fake_transport_cls):
    """The backend ranks on full text; our haystack is narrower. Re-filtering
    here would drop postings whose match was in a field we don't store."""
    provider = WorkingNomadsProvider(fake_transport_cls())
    result = provider.search(JobSearchQuery(keywords=["ppc"]))
    assert len(result.postings) == 2


def test_search_still_applies_the_filters_the_backend_cannot(fake_transport_cls):
    provider = WorkingNomadsProvider(fake_transport_cls())
    result = provider.search(JobSearchQuery(min_salary=60_000))
    assert {p.external_id for p in result.postings} == {"1752874"}


def test_search_respects_the_limit(fake_transport_cls):
    provider = WorkingNomadsProvider(fake_transport_cls())
    assert len(provider.search(JobSearchQuery(limit=1)).postings) == 1


def test_health_check_reports_healthy_on_success(fake_transport_cls):
    assert WorkingNomadsProvider(fake_transport_cls()).health_check().status == HealthStatus.HEALTHY


def test_health_check_reports_down_when_the_backend_raises(fake_transport_cls):
    provider = WorkingNomadsProvider(fake_transport_cls(raise_error=RuntimeError("503")))
    health = provider.health_check()
    assert health.status == HealthStatus.DOWN
    assert "503" in health.detail


def test_health_check_asks_for_a_single_document(fake_transport_cls):
    """Health checks run before every search — they must stay cheap."""
    transport = fake_transport_cls()
    WorkingNomadsProvider(transport).health_check()
    assert transport.search_calls[0]["size"] == 1
