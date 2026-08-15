"""Tests for click-only job search + application generation. No real
network calls: a fake provider stands in for RemoteOK/Arbeitnow.
"""

from __future__ import annotations

from careeros_career_brain import CareerBrain, CareerBrainRepository, Identity
from careeros_dashboard.search_actions import generate_application_for_job, search_for_jobs
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


def _make_posting(**overrides) -> JobPosting:
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


def _make_brain(store) -> CareerBrain:
    brain = CareerBrain(identity=Identity(full_name="Ada Lovelace", email="ada@example.com"))
    CareerBrainRepository(store).save(brain)
    return brain


def test_search_for_jobs_discovers_and_qualifies(store):
    brain = _make_brain(store)
    registry = JobProviderRegistry()
    registry.register(FakeProvider([_make_posting()]))

    summary = search_for_jobs(
        store,
        brain.identity.id,
        keywords=[],
        remote_only=False,
        limit=25,
        provider_registry=registry,
    )

    assert summary["discovered"] == 1


def test_generate_application_for_job_builds_a_real_package(store):
    brain = _make_brain(store)
    registry = JobProviderRegistry()
    registry.register(FakeProvider([_make_posting(url="https://example.com/jobs/42")]))

    package = generate_application_for_job(
        store, brain.identity.id, "https://example.com/jobs/42", provider_registry=registry
    )

    assert package is not None
    assert "Ada Lovelace" in package.resume_text


def test_generate_application_for_unknown_job_url_returns_none(store):
    brain = _make_brain(store)
    registry = JobProviderRegistry()
    registry.register(FakeProvider([_make_posting()]))

    package = generate_application_for_job(
        store, brain.identity.id, "https://example.com/does-not-exist", provider_registry=registry
    )

    assert package is None


def test_generate_application_for_unknown_identity_returns_none(store):
    registry = JobProviderRegistry()
    registry.register(FakeProvider([_make_posting()]))

    package = generate_application_for_job(
        store, "no-such-identity", "https://example.com/jobs/1", provider_registry=registry
    )

    assert package is None
