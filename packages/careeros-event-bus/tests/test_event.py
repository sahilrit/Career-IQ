"""Tests for the Event model."""

from __future__ import annotations

from careeros_event_bus import Event


def test_event_generates_a_unique_id_by_default():
    a = Event(event_type="job.discovered")
    b = Event(event_type="job.discovered")
    assert a.id != b.id


def test_event_payload_defaults_to_empty_dict():
    event = Event(event_type="job.discovered")
    assert event.payload == {}


def test_event_carries_arbitrary_payload():
    event = Event(event_type="job.discovered", payload={"job_id": "abc123"}, source="remoteok")
    assert event.payload["job_id"] == "abc123"
    assert event.source == "remoteok"
