"""Tests for wiring the Event Bus into HistoryLog."""

from __future__ import annotations

import pytest

from careeros_common import DocumentStore
from careeros_event_bus import Event, EventBus
from careeros_memory import HistoryLog, attach_history_logging


@pytest.fixture
def log():
    with DocumentStore() as store:
        yield HistoryLog(store)


def test_recognized_event_prefix_is_recorded(log):
    bus = EventBus()
    attach_history_logging(bus, log)

    bus.publish(
        Event(
            event_type="application.status_changed",
            payload={"subject_id": "app-1", "new_status": "applied"},
        )
    )

    entries = log.for_subject("application", "app-1")
    assert len(entries) == 1
    assert entries[0].summary == "application.status_changed"
    assert entries[0].details["new_status"] == "applied"


def test_unrecognized_event_prefix_is_ignored(log):
    bus = EventBus()
    attach_history_logging(bus, log)

    bus.publish(Event(event_type="system.heartbeat"))

    assert log.all() == []


@pytest.mark.parametrize(
    ("event_type", "expected_category"),
    [
        ("application.status_changed", "application"),
        ("company.researched", "company"),
        ("recruiter.contacted", "recruiter"),
        ("interview.scheduled", "interview"),
        ("outcome.recorded", "outcome"),
    ],
)
def test_every_documented_memory_category_is_wired_up(log, event_type, expected_category):
    bus = EventBus()
    attach_history_logging(bus, log)

    bus.publish(Event(event_type=event_type, payload={"subject_id": "x"}))

    assert log.by_category(expected_category)[0].summary == event_type


def test_falls_back_to_event_id_when_no_subject_id_in_payload(log):
    bus = EventBus()
    attach_history_logging(bus, log)

    event = Event(event_type="application.discovered", payload={})
    bus.publish(event)

    assert log.for_subject("application", event.id)[0].summary == "application.discovered"
