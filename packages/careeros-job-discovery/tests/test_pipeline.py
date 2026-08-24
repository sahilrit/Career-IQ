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


def _pipeline(repository, providers, *, llm_scorer=None, posting_repository=None):
    registry = JobProviderRegistry()
    for provider in providers:
        registry.register(provider)
    bus = EventBus()
    pipeline = JobDiscoveryPipeline(
        registry, repository, bus, posting_repository, llm_scorer=llm_scorer
    )
    return pipeline, bus


@pytest.fixture
def posting_repository():
    from careeros_job_discovery import JobPostingRepository

    with DocumentStore() as store:
        yield JobPostingRepository(store)


def test_run_stores_new_applications_on_the_brain(
    repository, brain_factory, posting_factory, fake_provider_cls
):
    brain = brain_factory()
    repository.save(brain)
    provider = fake_provider_cls("remoteok", [posting_factory()])
    pipeline, _bus = _pipeline(repository, [provider])

    new_applications = pipeline.run(brain.identity.id, JobSearchQuery()).applications

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
    second_run = pipeline.run(brain.identity.id, JobSearchQuery()).applications

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

    new_applications = pipeline.run(brain.identity.id, JobSearchQuery()).applications

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

    new_applications = pipeline.run(brain.identity.id, JobSearchQuery()).applications

    assert len(new_applications) == 2


def test_run_carries_provider_failures_through_to_the_caller(
    repository, brain_factory, posting_factory, fake_provider_cls
):
    """A source that breaks must not just quietly shrink the result set."""
    brain = brain_factory()
    repository.save(brain)
    working = fake_provider_cls("remoteok", [posting_factory()])
    broken = fake_provider_cls("linkedin", raise_on_search=True)
    pipeline, _bus = _pipeline(repository, [working, broken])

    run = pipeline.run(brain.identity.id, JobSearchQuery())

    assert len(run.applications) == 1
    assert any("linkedin" in error for error in run.source_errors)


def test_run_reports_no_errors_when_every_provider_works(
    repository, brain_factory, posting_factory, fake_provider_cls
):
    brain = brain_factory()
    repository.save(brain)
    pipeline, _bus = _pipeline(repository, [fake_provider_cls("remoteok", [posting_factory()])])

    assert pipeline.run(brain.identity.id, JobSearchQuery()).source_errors == []


# --- LLM scoring stage -------------------------------------------------------


class _StubScorer:
    """Stands in for LlmJobScorer without an AI client."""

    def __init__(self, result=None, *, only_above: float = 0.0) -> None:
        self._result = result
        self._only_above = only_above
        self.scored: list[str] = []

    def score(self, posting, *, profile_summary):
        self.scored.append(posting.url)
        return self._result


def test_the_llm_stage_is_optional(repository, brain_factory, posting_factory, fake_provider_cls):
    """Discovery works exactly as before when no scorer is configured."""
    brain = brain_factory()
    repository.save(brain)
    pipeline, _bus = _pipeline(repository, [fake_provider_cls("remoteok", [posting_factory()])])
    assert len(pipeline.run(brain.identity.id, JobSearchQuery()).applications) == 1


def test_the_llm_score_replaces_the_heuristic_one(
    repository, brain_factory, posting_factory, fake_provider_cls
):
    from careeros_job_discovery.llm_scoring import LlmScoreResult

    brain = brain_factory()
    repository.save(brain)
    scorer = _StubScorer(LlmScoreResult(score=91, reason="Strong overlap."))
    pipeline, _bus = _pipeline(
        repository, [fake_provider_cls("remoteok", [posting_factory()])], llm_scorer=scorer
    )

    run = pipeline.run(brain.identity.id, JobSearchQuery())

    assert scorer.scored
    # 0-100 from the model, normalised onto the same 0-1 scale the heuristic uses.
    assert run.applications[0].match_score == pytest.approx(0.91)


def test_a_failed_llm_score_falls_back_to_the_heuristic(
    repository, brain_factory, posting_factory, fake_provider_cls
):
    brain = brain_factory()
    repository.save(brain)
    scorer = _StubScorer(None)
    pipeline, _bus = _pipeline(
        repository, [fake_provider_cls("remoteok", [posting_factory()])], llm_scorer=scorer
    )

    run = pipeline.run(brain.identity.id, JobSearchQuery())

    assert len(run.applications) == 1
    assert run.applications[0].match_score is not None


def test_llm_patches_correct_the_cached_posting(
    repository, brain_factory, posting_factory, fake_provider_cls, posting_repository
):
    """A correction is only worth making if it reaches the cached posting the
    application generator reads back later."""
    from careeros_job_discovery.llm_scoring import JobFactPatch, LlmScoreResult

    brain = brain_factory()
    repository.save(brain)
    posting = posting_factory(description="This role is fully remote.", remote=False)
    result = LlmScoreResult(
        score=70,
        patches=[
            JobFactPatch(
                field="remote",
                value=True,
                confidence="high",
                evidence="This role is fully remote.",
            )
        ],
    )
    pipeline, _bus = _pipeline(
        repository,
        [fake_provider_cls("remoteok", [posting])],
        llm_scorer=_StubScorer(result),
        posting_repository=posting_repository,
    )

    pipeline.run(brain.identity.id, JobSearchQuery())

    assert posting_repository.load_or_none(posting.url).remote is True
