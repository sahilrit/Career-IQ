"""Shared fixtures for job agent tests."""

from __future__ import annotations

import pytest

from careeros_career_brain import CareerBrain, CareerBrainRepository, Identity, Skill
from careeros_common import DocumentStore
from careeros_event_bus import EventBus
from careeros_job_discovery import JobDiscoveryPipeline
from careeros_job_providers import (
    JobPosting,
    JobProvider,
    JobProviderRegistry,
    JobSearchQuery,
    JobSearchResult,
)


class FakeProvider(JobProvider):
    def __init__(self, provider_id: str, postings: list[JobPosting]) -> None:
        self._provider_id = provider_id
        self._postings = postings

    @property
    def provider_id(self) -> str:
        return self._provider_id

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        return JobSearchResult(postings=list(self._postings))


def make_posting(external_id: str = "1", **overrides) -> JobPosting:
    defaults = {
        "source_provider": "remoteok",
        "external_id": external_id,
        "title": "Backend Engineer",
        "company_name": "Acme",
        "url": f"https://example.com/jobs/{external_id}",
        "remote": True,
    }
    defaults.update(overrides)
    return JobPosting(**defaults)


@pytest.fixture
def high_scoring_posting():
    return make_posting(external_id="high", tags=["python", "django"])


@pytest.fixture
def low_scoring_posting():
    return make_posting(external_id="low", tags=["rust", "erlang"], title="Systems Engineer")


@pytest.fixture
def repository():
    with DocumentStore() as store:
        yield CareerBrainRepository(store)


@pytest.fixture
def brain_with_python_skills(repository):
    brain = CareerBrain(
        identity=Identity(full_name="Ada Lovelace", email="ada@example.com"),
        skills=[Skill(name="Python"), Skill(name="Django")],
    )
    repository.save(brain)
    return brain


@pytest.fixture
def event_bus():
    return EventBus()


def make_pipeline(repository, event_bus, postings: list[JobPosting]) -> JobDiscoveryPipeline:
    registry = JobProviderRegistry()
    registry.register(FakeProvider("remoteok", postings))
    return JobDiscoveryPipeline(registry, repository, event_bus)


@pytest.fixture
def pipeline_factory(repository, event_bus):
    def factory(postings: list[JobPosting]) -> JobDiscoveryPipeline:
        return make_pipeline(repository, event_bus, postings)

    return factory
