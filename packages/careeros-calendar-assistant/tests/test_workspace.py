"""Tests for EventWorkspace / EventWorkspaceRepository."""

from __future__ import annotations

import pytest

from careeros_calendar_assistant import EventWorkspace, EventWorkspaceRepository
from careeros_common import DocumentStore


@pytest.fixture
def repository():
    with DocumentStore() as store:
        yield EventWorkspaceRepository(store)


def test_save_then_load_roundtrips(repository):
    workspace = EventWorkspace(calendar_event_id="event-1", interview_notes="be confident")
    repository.save(workspace)
    assert repository.load(workspace.id).interview_notes == "be confident"


def test_for_calendar_event_finds_the_matching_workspace(repository):
    workspace = EventWorkspace(calendar_event_id="event-1")
    repository.save(workspace)
    found = repository.for_calendar_event("event-1")
    assert found is not None
    assert found.id == workspace.id


def test_for_calendar_event_returns_none_when_no_match(repository):
    assert repository.for_calendar_event("does-not-exist") is None


def test_default_fields_are_empty(repository):
    workspace = EventWorkspace(calendar_event_id="event-1")
    assert workspace.job_description == ""
    assert workspace.outreach_thread == []
    assert workspace.interviewer_info == {}
