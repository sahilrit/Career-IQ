"""Tests for wiring the relationship timeline to platform events."""

from __future__ import annotations

import pytest

from careeros_crm import RelationshipStage, wire_crm
from careeros_event_bus import Event, EventBus


@pytest.fixture
def wired_bus(timeline_repository):
    bus = EventBus()
    wire_crm(bus, timeline_repository)
    return bus


def test_company_qualified_marks_opportunity(wired_bus, timeline_repository):
    wired_bus.publish(Event(event_type="company.qualified", payload={"subject_id": "contact-1"}))
    assert timeline_repository.load("contact-1").current_stage == RelationshipStage.OPPORTUNITY


def test_client_won_marks_client_or_employer(wired_bus, timeline_repository):
    wired_bus.publish(Event(event_type="client.won", payload={"subject_id": "contact-1"}))
    assert (
        timeline_repository.load("contact-1").current_stage == RelationshipStage.CLIENT_OR_EMPLOYER
    )


def test_outcome_recorded_with_accepted_marks_client_or_employer(wired_bus, timeline_repository):
    wired_bus.publish(
        Event(
            event_type="outcome.recorded",
            payload={"subject_id": "contact-1", "final_status": "accepted"},
        )
    )
    assert (
        timeline_repository.load("contact-1").current_stage == RelationshipStage.CLIENT_OR_EMPLOYER
    )


def test_outcome_recorded_with_unmapped_status_is_ignored(wired_bus, timeline_repository):
    wired_bus.publish(
        Event(
            event_type="outcome.recorded",
            payload={"subject_id": "contact-1", "final_status": "rejected"},
        )
    )
    assert timeline_repository.load("contact-1").current_stage is None


def test_unrelated_events_are_ignored(wired_bus, timeline_repository):
    wired_bus.publish(Event(event_type="system.heartbeat", payload={}))
    assert timeline_repository.load("contact-1").current_stage is None


def test_event_missing_subject_id_does_not_raise(wired_bus):
    wired_bus.publish(Event(event_type="company.qualified", payload={}))  # must not raise
