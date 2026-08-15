"""Tests for ArbeitnowProvider, entirely against a fake transport."""

from __future__ import annotations

from careeros_arbeitnow_provider import ArbeitnowProvider
from careeros_job_providers import HealthStatus, JobSearchQuery


def test_provider_id_is_arbeitnow():
    provider = ArbeitnowProvider(transport=None)
    assert provider.provider_id == "arbeitnow"


def test_search_returns_every_posting(fake_transport_cls):
    provider = ArbeitnowProvider(transport=fake_transport_cls())
    result = provider.search(JobSearchQuery())
    assert len(result.postings) == 2
    assert {p.external_id for p in result.postings} == {
        "senior-backend-engineer-acme",
        "frontend-engineer-widgetco",
    }


def test_search_applies_the_query_filter(fake_transport_cls):
    provider = ArbeitnowProvider(transport=fake_transport_cls())
    result = provider.search(JobSearchQuery(keywords=["react"]))
    assert len(result.postings) == 1
    assert result.postings[0].title == "Frontend Engineer"


def test_search_respects_the_limit(fake_transport_cls):
    provider = ArbeitnowProvider(transport=fake_transport_cls())
    result = provider.search(JobSearchQuery(limit=1))
    assert len(result.postings) == 1


def test_search_respects_remote_only(fake_transport_cls):
    provider = ArbeitnowProvider(transport=fake_transport_cls())
    result = provider.search(JobSearchQuery(remote_only=True))
    assert len(result.postings) == 1
    assert result.postings[0].title == "Senior Backend Engineer"


def test_health_check_reports_healthy_on_success(fake_transport_cls):
    provider = ArbeitnowProvider(transport=fake_transport_cls())
    health = provider.health_check()
    assert health.status == HealthStatus.HEALTHY


def test_health_check_reports_down_when_transport_raises(fake_transport_cls):
    provider = ArbeitnowProvider(transport=fake_transport_cls(raise_error=RuntimeError("timeout")))
    health = provider.health_check()
    assert health.status == HealthStatus.DOWN
    assert "timeout" in health.detail
