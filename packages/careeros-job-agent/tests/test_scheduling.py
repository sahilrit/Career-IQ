"""Tests for wiring a JobAgent onto a Runtime as a recurring job."""

from __future__ import annotations

from datetime import UTC, datetime

from careeros_career_brain import ApplicationStatus
from careeros_job_agent import DEFAULT_JOB_NAME, JobAgent, register_job_agent
from careeros_job_providers import JobSearchQuery
from careeros_runtime import Runtime


def test_registered_agent_runs_a_cycle_when_due(
    repository, event_bus, brain_with_python_skills, pipeline_factory, high_scoring_posting
):
    pipeline = pipeline_factory([high_scoring_posting])
    agent = JobAgent(pipeline, repository, event_bus)
    runtime = Runtime(worker_pool_size=1)
    runtime.start()
    try:
        start = datetime(2026, 1, 1, tzinfo=UTC)
        register_job_agent(
            runtime,
            agent,
            brain_with_python_skills.identity.id,
            JobSearchQuery(),
            interval_seconds=3600,
            start_at=start,
        )

        assert runtime.run_due_jobs(now=start) == 1
        runtime.wait_idle()

        reloaded = repository.load(brain_with_python_skills.identity.id)
        assert reloaded.applications[0].status == ApplicationStatus.QUALIFIED
    finally:
        runtime.stop()


def test_default_job_name_is_registered(
    repository, event_bus, brain_with_python_skills, pipeline_factory, high_scoring_posting
):
    pipeline = pipeline_factory([high_scoring_posting])
    agent = JobAgent(pipeline, repository, event_bus)
    runtime = Runtime(worker_pool_size=1)

    register_job_agent(runtime, agent, brain_with_python_skills.identity.id, JobSearchQuery())

    assert runtime.health().registered_jobs == [DEFAULT_JOB_NAME]


def test_custom_job_name_and_interval_are_respected(
    repository, event_bus, brain_with_python_skills, pipeline_factory, high_scoring_posting
):
    pipeline = pipeline_factory([high_scoring_posting])
    agent = JobAgent(pipeline, repository, event_bus)
    runtime = Runtime(worker_pool_size=1)

    register_job_agent(
        runtime,
        agent,
        brain_with_python_skills.identity.id,
        JobSearchQuery(),
        interval_seconds=120,
        job_name="my-job-agent",
    )

    assert runtime.health().registered_jobs == ["my-job-agent"]
