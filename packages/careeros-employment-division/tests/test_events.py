"""Tests for wiring pipeline progress to events from earlier phases."""

from __future__ import annotations

import pytest

from careeros_employment_division import (
    PipelineProgressRepository,
    PipelineStage,
    wire_pipeline_progress,
)
from careeros_event_bus import Event, EventBus


@pytest.fixture
def progress_repository(store):
    return PipelineProgressRepository(store)


@pytest.fixture
def wired_bus(progress_repository):
    bus = EventBus()
    wire_pipeline_progress(bus, progress_repository)
    return bus


def test_application_created_marks_discovery(wired_bus, progress_repository):
    wired_bus.publish(Event(event_type="application.created", payload={"subject_id": "app-1"}))
    assert progress_repository.load("app-1").current_stage == PipelineStage.DISCOVERY


def test_job_scored_marks_scoring(wired_bus, progress_repository):
    wired_bus.publish(Event(event_type="job.scored", payload={"subject_id": "app-1"}))
    assert progress_repository.load("app-1").current_stage == PipelineStage.SCORING


def test_autonomously_submitted_marks_application(wired_bus, progress_repository):
    wired_bus.publish(
        Event(event_type="application.autonomously_submitted", payload={"subject_id": "app-1"})
    )
    assert progress_repository.load("app-1").current_stage == PipelineStage.APPLICATION


@pytest.mark.parametrize(
    ("final_status", "expected_stage"),
    [
        ("interviewing", PipelineStage.INTERVIEW),
        ("offer", PipelineStage.OFFER),
        ("accepted", PipelineStage.NEGOTIATION),
    ],
)
def test_outcome_recorded_marks_the_matching_stage(
    wired_bus, progress_repository, final_status, expected_stage
):
    wired_bus.publish(
        Event(
            event_type="outcome.recorded",
            payload={"subject_id": "app-1", "final_status": final_status},
        )
    )
    assert progress_repository.load("app-1").current_stage == expected_stage


def test_outcome_recorded_with_unmapped_status_is_ignored(wired_bus, progress_repository):
    wired_bus.publish(
        Event(
            event_type="outcome.recorded",
            payload={"subject_id": "app-1", "final_status": "rejected"},
        )
    )
    assert progress_repository.load("app-1").current_stage is None


def test_unrelated_events_are_ignored(wired_bus, progress_repository):
    wired_bus.publish(Event(event_type="system.heartbeat", payload={}))
    assert progress_repository.load("app-1").current_stage is None


def test_event_missing_subject_id_does_not_raise(wired_bus):
    wired_bus.publish(Event(event_type="job.scored", payload={}))  # must not raise
