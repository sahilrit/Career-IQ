"""Tests for JobDiscoveryPipeline: discover -> score -> store -> emit."""

from __future__ import annotations

import pytest

from careeros_career_brain import ApplicationStatus, CareerBrainRepository
from careeros_common import DocumentStore
from careeros_event_bus import EventBus
from careeros_job_discovery import JobDiscoveryPipeline
from careeros_job_providers import JobProviderRegistry, JobSearchQuery


@pytest.fixture
def repository():
    with DocumentStore() as store:
        yield CareerBrainRepository(store)


def _pipeline(repository, providers):
    registry = JobProviderRegistry()
    for provider in providers:
        registry.register(provider)
    bus = EventBus()
    return JobDiscoveryPipeline(registry, repository, bus), bus


def test_run_stores_new_applications_on_the_brain(
    repository, brain_factory, posting_factory, fake_provider_cls
):
    brain = brain_factory()
    repository.save(brain)
    provider = fake_provider_cls("remoteok", [posting_factory()])
    pipeline, _bus = _pipeline(repository, [provider])

    new_applications = pipeline.run(brain.identity.id, JobSearchQuery())

    assert len(new_applications) == 1
    reloaded = repository.load(brain.identity.id)
    assert len(reloaded.applications) == 1
    assert reloaded.applications[0].status == ApplicationStatus.DISCOVERED
    assert reloaded.applications[0].match_score is not None


def test_running_twice_does_not_duplicate_the_same_posting(
    repository, brain_factory, posting_factory, fake_provider_cls
):
    brain = brain_factory()
    repository.save(brain)
    provider = fake_provider_cls("remoteok", [posting_factory()])
    pipeline, _bus = _pipeline(repository, [provider])

    pipeline.run(brain.identity.id, JobSearchQuery())
    second_run = pipeline.run(brain.identity.id, JobSearchQuery())

    assert second_run == []
    reloaded = repository.load(brain.identity.id)
    assert len(reloaded.applications) == 1


def test_run_publishes_discovered_scored_and_created_events(
    repository, brain_factory, posting_factory, fake_provider_cls
):
    brain = brain_factory()
    repository.save(brain)
    provider = fake_provider_cls("remoteok", [posting_factory()])
    pipeline, bus = _pipeline(repository, [provider])

    pipeline.run(brain.identity.id, JobSearchQuery())

    event_types = [e.event_type for e in bus.history()]
    assert event_types == ["job.discovered", "job.scored", "application.created"]


def test_run_with_no_matching_postings_does_not_touch_the_repository(
    repository, brain_factory, fake_provider_cls
):
    brain = brain_factory()
    repository.save(brain)
    provider = fake_provider_cls("remoteok", [])
    pipeline, _bus = _pipeline(repository, [provider])

    new_applications = pipeline.run(brain.identity.id, JobSearchQuery())

    assert new_applications == []
    assert repository.load(brain.identity.id).applications == []


def test_run_aggregates_across_multiple_providers(
    repository, brain_factory, posting_factory, fake_provider_cls
):
    brain = brain_factory()
    repository.save(brain)
    a = fake_provider_cls(
        "remoteok", [posting_factory(source_provider="remoteok", external_id="1")]
    )
    b = fake_provider_cls(
        "wellfound",
        [
            posting_factory(
                source_provider="wellfound",
                external_id="2",
                url="https://example.com/jobs/2",
            )
        ],
    )
    pipeline, _bus = _pipeline(repository, [a, b])

    new_applications = pipeline.run(brain.identity.id, JobSearchQuery())

    assert len(new_applications) == 2
