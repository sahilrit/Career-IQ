"""Tests for `careeros search` command logic, against a fake provider."""

from __future__ import annotations

from careeros_career_brain import CareerBrain, Identity, Skill
from careeros_cli.commands.search import run_search
from careeros_job_providers import JobSearchQuery


def test_run_search_discovers_and_qualifies_a_matching_posting(context):
    brain = CareerBrain(
        identity=Identity(full_name="Ada", email="ada@example.com"),
        skills=[Skill(name="Python", proficiency=5)],
    )
    context.repository.save(brain)

    summary = run_search(context, brain.identity.id, JobSearchQuery())

    assert summary["discovered"] == 1
    assert summary["qualified"] == 1


def test_run_search_a_second_time_finds_nothing_new(context):
    brain = CareerBrain(identity=Identity(full_name="Ada", email="ada@example.com"))
    context.repository.save(brain)

    run_search(context, brain.identity.id, JobSearchQuery())
    second = run_search(context, brain.identity.id, JobSearchQuery())

    assert second == {"discovered": 0, "qualified": 0}
