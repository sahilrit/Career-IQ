"""Tests for the AutonomousAgencyDivision facade."""

from __future__ import annotations

from careeros_autonomous_agency import AgencyStage, AutonomousAgencyDivision
from careeros_event_bus import Event, EventBus


def test_progress_for_a_new_subject_starts_at_employment(store):
    division = AutonomousAgencyDivision(store)
    progress = division.progress_for("u-1")
    assert progress.next_stage == AgencyStage.EMPLOYMENT


def test_mark_complete_advances_progress(store):
    division = AutonomousAgencyDivision(store)
    progress = division.mark_complete("u-1", AgencyStage.PERSONAL_BRAND)
    assert progress.current_stage == AgencyStage.PERSONAL_BRAND


def test_without_an_event_bus_events_do_nothing(store):
    division = AutonomousAgencyDivision(store)
    bus = EventBus()
    bus.publish(Event(event_type="client.won", payload={"subject_id": "u-1"}))
    assert division.progress_for("u-1").current_stage is None


def test_with_an_event_bus_real_events_advance_progress(store):
    bus = EventBus()
    division = AutonomousAgencyDivision(store, event_bus=bus)
    bus.publish(Event(event_type="client.won", payload={"subject_id": "u-1"}))
    assert division.progress_for("u-1").current_stage == AgencyStage.FREELANCE


def test_full_lap_then_start_new_cycle(store):
    division = AutonomousAgencyDivision(store)
    for stage in AgencyStage:
        division.mark_complete("u-1", stage)

    progress = division.start_new_cycle("u-1")
    assert progress.cycles_completed == 1
    assert progress.next_stage == AgencyStage.EMPLOYMENT
