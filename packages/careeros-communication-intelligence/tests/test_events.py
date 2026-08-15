"""Tests for process_message/process_all: Email -> Classification -> Event."""

from __future__ import annotations

from datetime import UTC, datetime

from careeros_communication_intelligence import (
    CommunicationCategory,
    EmailMessage,
    process_all,
    process_message,
)
from careeros_event_bus import EventBus


def _message(**overrides) -> EmailMessage:
    defaults = {
        "id": "email-1",
        "sender": "recruiter@acme.example",
        "subject": "Interview invitation",
        "body": "We'd like to schedule a call for a technical screen.",
        "received_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    return EmailMessage(**defaults)


def test_process_message_publishes_the_matching_event():
    bus = EventBus()
    category = process_message(_message(), bus)

    assert category == CommunicationCategory.INTERVIEW
    events = [e for e in bus.history() if e.event_type == "communication.interview_detected"]
    assert len(events) == 1
    assert events[0].payload["subject_id"] == "email-1"


def test_process_message_with_other_category_publishes_nothing():
    bus = EventBus()
    category = process_message(
        _message(subject="Your order shipped", body="Your package is on its way."), bus
    )

    assert category == CommunicationCategory.OTHER
    assert bus.history() == []


def test_process_all_classifies_every_message_from_the_provider():
    class FakeProvider:
        def fetch_new_messages(self) -> list[EmailMessage]:
            return [
                _message(id="1", subject="Offer", body="We are pleased to offer you the role."),
                _message(id="2", subject="Unrelated", body="Your package shipped."),
            ]

    bus = EventBus()
    categories = process_all(FakeProvider(), bus)

    assert categories == [CommunicationCategory.OFFER, CommunicationCategory.OTHER]
    assert len(bus.history()) == 1
