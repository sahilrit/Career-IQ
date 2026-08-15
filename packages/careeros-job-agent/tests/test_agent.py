"""Tests for JobAgent.run_cycle: discover -> score -> qualify -> emit."""

from __future__ import annotations

from careeros_career_brain import ApplicationStatus
from careeros_job_agent import JobAgent
from careeros_job_providers import JobSearchQuery


def test_high_scoring_posting_is_qualified(
    repository, event_bus, brain_with_python_skills, pipeline_factory, high_scoring_posting
):
    pipeline = pipeline_factory([high_scoring_posting])
    agent = JobAgent(pipeline, repository, event_bus)

    summary = agent.run_cycle(brain_with_python_skills.identity.id, JobSearchQuery())

    assert summary == {"discovered": 1, "qualified": 1}
    reloaded = repository.load(brain_with_python_skills.identity.id)
    assert reloaded.applications[0].status == ApplicationStatus.QUALIFIED


def test_low_scoring_posting_stays_discovered(
    repository, event_bus, brain_with_python_skills, pipeline_factory, low_scoring_posting
):
    pipeline = pipeline_factory([low_scoring_posting])
    agent = JobAgent(pipeline, repository, event_bus)

    summary = agent.run_cycle(brain_with_python_skills.identity.id, JobSearchQuery())

    assert summary == {"discovered": 1, "qualified": 0}
    reloaded = repository.load(brain_with_python_skills.identity.id)
    assert reloaded.applications[0].status == ApplicationStatus.DISCOVERED


def test_qualification_publishes_a_status_changed_event(
    repository, event_bus, brain_with_python_skills, pipeline_factory, high_scoring_posting
):
    pipeline = pipeline_factory([high_scoring_posting])
    agent = JobAgent(pipeline, repository, event_bus)

    agent.run_cycle(brain_with_python_skills.identity.id, JobSearchQuery())

    status_events = [e for e in event_bus.history() if e.event_type == "application.status_changed"]
    assert len(status_events) == 1
    assert status_events[0].payload["new_status"] == "qualified"


def test_low_scoring_posting_publishes_no_status_changed_event(
    repository, event_bus, brain_with_python_skills, pipeline_factory, low_scoring_posting
):
    pipeline = pipeline_factory([low_scoring_posting])
    agent = JobAgent(pipeline, repository, event_bus)

    agent.run_cycle(brain_with_python_skills.identity.id, JobSearchQuery())

    status_events = [e for e in event_bus.history() if e.event_type == "application.status_changed"]
    assert status_events == []


def test_second_cycle_with_same_postings_discovers_nothing_new(
    repository, event_bus, brain_with_python_skills, pipeline_factory, high_scoring_posting
):
    pipeline = pipeline_factory([high_scoring_posting])
    agent = JobAgent(pipeline, repository, event_bus)

    agent.run_cycle(brain_with_python_skills.identity.id, JobSearchQuery())
    second = agent.run_cycle(brain_with_python_skills.identity.id, JobSearchQuery())

    assert second == {"discovered": 0, "qualified": 0}


def test_mixed_batch_qualifies_only_the_high_scoring_posting(
    repository,
    event_bus,
    brain_with_python_skills,
    pipeline_factory,
    high_scoring_posting,
    low_scoring_posting,
):
    pipeline = pipeline_factory([high_scoring_posting, low_scoring_posting])
    agent = JobAgent(pipeline, repository, event_bus)

    summary = agent.run_cycle(brain_with_python_skills.identity.id, JobSearchQuery())

    assert summary == {"discovered": 2, "qualified": 1}
