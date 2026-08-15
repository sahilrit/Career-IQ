"""Shared fixtures for job provider framework tests."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from careeros_job_providers import (
    HealthStatus,
    JobPosting,
    JobProvider,
    JobSearchQuery,
    JobSearchResult,
    ProviderHealth,
)


class FakeProvider(JobProvider):
    def __init__(
        self,
        provider_id: str,
        postings: list[JobPosting] | None = None,
        *,
        health: HealthStatus = HealthStatus.HEALTHY,
        raise_on_search: bool = False,
    ) -> None:
        self._provider_id = provider_id
        self._postings = postings or []
        self._health = health
        self._raise_on_search = raise_on_search
        self.search_calls = 0

    @property
    def provider_id(self) -> str:
        return self._provider_id

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        self.search_calls += 1
        if self._raise_on_search:
            raise RuntimeError("provider is on fire")
        return JobSearchResult(postings=list(self._postings))

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(status=self._health)


def make_posting(
    source_provider: str = "fake",
    external_id: str = "1",
    title: str = "Backend Engineer",
    **overrides: object,
) -> JobPosting:
    defaults = {
        "source_provider": source_provider,
        "external_id": external_id,
        "title": title,
        "company_name": "Acme",
        "url": f"https://example.com/jobs/{external_id}",
    }
    defaults.update(overrides)
    return JobPosting(**defaults)


@pytest.fixture
def posting_factory() -> Callable[..., JobPosting]:
    return make_posting


@pytest.fixture
def fake_provider_cls() -> type[FakeProvider]:
    return FakeProvider
