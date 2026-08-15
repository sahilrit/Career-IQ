"""Tests for wiring agency-cycle progress to events from earlier phases."""

from __future__ import annotations

import pytest

from careeros_autonomous_agency import (
    AgencyCycleProgressRepository,
    AgencyStage,
    wire_agency_cycle,
)
from careeros_event_bus import Event, EventBus


@pytest.fixture
def progress_repository(store):
    return AgencyCycleProgressRepository(store)


@pytest.fixture
def wired_bus(progress_repository):
    bus = EventBus()
    wire_agency_cycle(bus, progress_repository)
    return bus


def test_autonomously_submitted_marks_employment(wired_bus, progress_repository):
    wired_bus.publish(
        Event(event_type="application.autonomously_submitted", payload={"subject_id": "u-1"})
    )
    assert progress_repository.load("u-1").current_stage == AgencyStage.EMPLOYMENT


def test_client_won_marks_freelance(wired_bus, progress_repository):
    wired_bus.publish(Event(event_type="client.won", payload={"subject_id": "u-1"}))
    assert progress_repository.load("u-1").current_stage == AgencyStage.FREELANCE


def test_company_qualified_marks_networking(wired_bus, progress_repository):
    wired_bus.publish(Event(event_type="company.qualified", payload={"subject_id": "u-1"}))
    assert progress_repository.load("u-1").current_stage == AgencyStage.NETWORKING


def test_unrelated_events_are_ignored(wired_bus, progress_repository):
    wired_bus.publish(Event(event_type="system.heartbeat", payload={}))
    assert progress_repository.load("u-1").current_stage is None


def test_event_missing_subject_id_does_not_raise(wired_bus):
    wired_bus.publish(Event(event_type="client.won", payload={}))  # must not raise


def test_furthest_reached_survives_events_arriving_out_of_order(wired_bus, progress_repository):
    wired_bus.publish(Event(event_type="company.qualified", payload={"subject_id": "u-1"}))
    wired_bus.publish(
        Event(event_type="application.autonomously_submitted", payload={"subject_id": "u-1"})
    )
    progress = progress_repository.load("u-1")
    assert progress.current_stage == AgencyStage.NETWORKING
    assert set(progress.completed_stages) == {AgencyStage.EMPLOYMENT, AgencyStage.NETWORKING}
