"""Shared fixtures for job discovery pipeline tests."""

from __future__ import annotations

import pytest

from careeros_career_brain import CareerBrain, Identity, Preferences, Skill
from careeros_job_providers import JobPosting, JobProvider, JobSearchQuery, JobSearchResult


def make_brain(**overrides) -> CareerBrain:
    defaults = {
        "identity": Identity(full_name="Ada Lovelace", email="ada@example.com"),
        "skills": [Skill(name="Python"), Skill(name="Django")],
        "preferences": Preferences(),
    }
    defaults.update(overrides)
    return CareerBrain(**defaults)


def make_posting(**overrides) -> JobPosting:
    defaults = {
        "source_provider": "remoteok",
        "external_id": "1",
        "title": "Senior Python Engineer",
        "company_name": "Acme",
        "url": "https://example.com/jobs/1",
        "tags": ["python", "django"],
        "remote": True,
    }
    defaults.update(overrides)
    return JobPosting(**defaults)


class FakeProvider(JobProvider):
    def __init__(self, provider_id: str, postings: list[JobPosting]) -> None:
        self._provider_id = provider_id
        self._postings = postings

    @property
    def provider_id(self) -> str:
        return self._provider_id

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        return JobSearchResult(postings=list(self._postings))


@pytest.fixture
def brain_factory():
    return make_brain


@pytest.fixture
def posting_factory():
    return make_posting


@pytest.fixture
def fake_provider_cls():
    return FakeProvider
