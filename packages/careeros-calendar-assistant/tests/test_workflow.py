"""Tests for the full Interview Email -> CalendarEvent -> EventWorkspace workflow."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from careeros_calendar_assistant import (
    CalendarEventRepository,
    EventWorkspaceRepository,
    process_interview_email,
)
from careeros_common import DocumentStore
from careeros_communication_intelligence import EmailMessage


@pytest.fixture
def repos():
    with DocumentStore() as store:
        yield CalendarEventRepository(store), EventWorkspaceRepository(store)


def _message(**overrides) -> EmailMessage:
    defaults = {
        "id": "email-1",
        "sender": "recruiter@acme.example",
        "subject": "Technical interview",
        "body": "Join us via https://zoom.us/j/123 on January 12, 2026 at 2:00 PM EST.",
        "received_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    return EmailMessage(**defaults)


def test_interview_email_creates_a_calendar_event_and_workspace(repos):
    calendar_repo, workspace_repo = repos
    event = process_interview_email(
        _message(), calendar_repo, workspace_repo, application_id="app-1"
    )

    assert event is not None
    assert event.application_id == "app-1"
    assert event.platform == "zoom"

    reloaded = calendar_repo.load(event.id)
    assert reloaded.title == "Technical interview"

    workspace = workspace_repo.for_calendar_event(event.id)
    assert workspace is not None


def test_non_interview_email_is_ignored(repos):
    calendar_repo, workspace_repo = repos
    non_interview = _message(subject="Your order shipped", body="Your package is on its way.")

    result = process_interview_email(non_interview, calendar_repo, workspace_repo)

    assert result is None
    assert calendar_repo.list_all() == []


def test_rejection_email_is_not_mistaken_for_an_interview(repos):
    calendar_repo, workspace_repo = repos
    rejection = _message(
        subject="Update on your application",
        body=(
            "Unfortunately, after your interview, we've decided to move "
            "forward with other candidates."
        ),
    )

    result = process_interview_email(rejection, calendar_repo, workspace_repo)

    assert result is None
