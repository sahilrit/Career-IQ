"""Tests for CalendarEvent / CalendarEventRepository."""

from __future__ import annotations

import pytest

from careeros_calendar_assistant import (
    CalendarEventRepository,
    InterviewDetails,
    InterviewStage,
    build_calendar_event,
)
from careeros_common import DocumentStore


@pytest.fixture
def repository():
    with DocumentStore() as store:
        yield CalendarEventRepository(store)


def test_build_calendar_event_copies_details_fields():
    details = InterviewDetails(
        timezone="America/New_York", platform="zoom", stage=InterviewStage.TECHNICAL
    )
    event = build_calendar_event("Interview", details, application_id="app-1")
    assert event.title == "Interview"
    assert event.application_id == "app-1"
    assert event.timezone == "America/New_York"
    assert event.stage == InterviewStage.TECHNICAL


def test_save_then_load_roundtrips(repository):
    event = build_calendar_event("Interview", InterviewDetails())
    repository.save(event)
    assert repository.load(event.id).title == "Interview"


def test_load_or_none_returns_none_when_missing(repository):
    assert repository.load_or_none("does-not-exist") is None


def test_for_application_filters(repository):
    a = build_calendar_event("A", InterviewDetails(), application_id="app-1")
    b = build_calendar_event("B", InterviewDetails(), application_id="app-2")
    repository.save(a)
    repository.save(b)
    assert [e.title for e in repository.for_application("app-1")] == ["A"]


def test_list_all_returns_every_event(repository):
    repository.save(build_calendar_event("A", InterviewDetails()))
    repository.save(build_calendar_event("B", InterviewDetails()))
    assert len(repository.list_all()) == 2
