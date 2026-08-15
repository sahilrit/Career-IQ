"""Shared fixtures for CLI tests. No real network calls: a FakeProvider
stands in for RemoteOKProvider everywhere a provider is needed.
"""

from __future__ import annotations

import pytest

from careeros_cli.context import build_context
from careeros_job_providers import (
    JobPosting,
    JobProvider,
    JobProviderRegistry,
    JobSearchQuery,
    JobSearchResult,
)


class FakeProvider(JobProvider):
    def __init__(self, postings: list[JobPosting]) -> None:
        self._postings = postings

    @property
    def provider_id(self) -> str:
        return "fake"

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        return JobSearchResult(postings=list(self._postings))


def make_posting(**overrides) -> JobPosting:
    defaults = {
        "source_provider": "fake",
        "external_id": "1",
        "title": "Backend Engineer",
        "company_name": "Acme",
        "url": "https://example.com/jobs/1",
        "tags": ["python"],
        "remote": True,
    }
    defaults.update(overrides)
    return JobPosting(**defaults)


@pytest.fixture
def posting_factory():
    return make_posting


@pytest.fixture
def fake_registry(posting_factory):
    registry = JobProviderRegistry()
    registry.register(FakeProvider([posting_factory()]))
    return registry


@pytest.fixture
def context(tmp_path, fake_registry):
    return build_context(tmp_path, provider_registry=fake_registry)
