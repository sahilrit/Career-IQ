"""Tests for the reply-tracking sync loop.

The loop reads recent recruiter email, matches each message to an open
application by company, and applies the stage the message signals —
respecting the same transition rules a human is held to.
"""

from __future__ import annotations

import pytest

from careeros_career_brain import (
    Application,
    ApplicationStatus,
    CareerBrain,
    CareerBrainRepository,
    Identity,
)
from careeros_common import DocumentStore
from careeros_event_bus import EventBus
from careeros_reply_tracking.sync import EmailMessage, sync_replies


class FakeMailbox:
    def __init__(self, messages: list[EmailMessage]) -> None:
        self._messages = messages
        self.calls = 0

    def recent_messages(self, *, days: int, max_messages: int) -> list[EmailMessage]:
        self.calls += 1
        return list(self._messages)


@pytest.fixture
def store():
    with DocumentStore() as document_store:
        yield document_store


@pytest.fixture
def brain_with_application(store):
    repository = CareerBrainRepository(store)
    brain = CareerBrain(identity=Identity(full_name="Sahil Sachdeva", email="sahil@example.com"))
    brain.applications.append(
        Application(
            job_title="Performance Marketing Manager",
            company_name="Acme Corp",
            job_url="https://example.com/jobs/1",
            status=ApplicationStatus.APPLIED,
        )
    )
    repository.save(brain)
    return brain


def _msg(**overrides) -> EmailMessage:
    defaults = {
        "id": "m1",
        "sender": "recruiting@acmecorp.com",
        "subject": "Your application to Acme Corp",
        "body": "We'd like to invite you to an interview next week.",
    }
    defaults.update(overrides)
    return EmailMessage(**defaults)


def _reload(store, identity_id):
    return CareerBrainRepository(store).load(identity_id)


def test_an_interview_email_advances_a_matching_application(store, brain_with_application):
    mailbox = FakeMailbox([_msg()])
    summary = sync_replies(store, brain_with_application.identity.id, mailbox, event_bus=EventBus())

    reloaded = _reload(store, brain_with_application.identity.id)
    app = reloaded.applications[0]
    # APPLIED -> IN_REVIEW -> INTERVIEWING is walked automatically; the target
    # is reached even though it is more than one hop away.
    assert app.status is ApplicationStatus.INTERVIEWING
    assert summary.transitioned == 1


def test_a_rejection_email_rejects_the_application(store, brain_with_application):
    mailbox = FakeMailbox([_msg(body="Unfortunately we won't be progressing your application.")])
    sync_replies(store, brain_with_application.identity.id, mailbox, event_bus=EventBus())

    app = _reload(store, brain_with_application.identity.id).applications[0]
    assert app.status is ApplicationStatus.REJECTED


def test_the_company_is_matched_case_and_suffix_insensitively(store, brain_with_application):
    """'Acme Corp' in the brain, 'ACME' in the email domain — still a match."""
    mailbox = FakeMailbox(
        [_msg(sender="talent@acme.io", subject="ACME interview", body="Let's schedule a call.")]
    )
    summary = sync_replies(store, brain_with_application.identity.id, mailbox, event_bus=EventBus())
    assert summary.transitioned == 1


def test_an_email_for_an_unknown_company_is_ignored(store, brain_with_application):
    mailbox = FakeMailbox(
        [_msg(sender="hr@otherco.com", subject="OtherCo", body="We'd like to interview you.")]
    )
    summary = sync_replies(store, brain_with_application.identity.id, mailbox, event_bus=EventBus())

    assert summary.transitioned == 0
    assert _reload(store, brain_with_application.identity.id).applications[0].status is (
        ApplicationStatus.APPLIED
    )


def test_a_neutral_email_changes_nothing(store, brain_with_application):
    mailbox = FakeMailbox([_msg(body="Thanks for applying, we have received your application.")])
    summary = sync_replies(store, brain_with_application.identity.id, mailbox, event_bus=EventBus())
    assert summary.transitioned == 0


def test_an_illegal_transition_is_skipped_not_forced(store):
    """A rejection email for an application already ACCEPTED must not move it —
    the transition rules forbid it, and the loop respects them."""
    repository = CareerBrainRepository(store)
    brain = CareerBrain(identity=Identity(full_name="Sahil", email="sahil@example.com"))
    brain.applications.append(
        Application(
            job_title="X",
            company_name="Acme Corp",
            status=ApplicationStatus.ACCEPTED,
        )
    )
    repository.save(brain)

    mailbox = FakeMailbox([_msg(body="Unfortunately we won't be progressing.")])
    summary = sync_replies(store, brain.identity.id, mailbox, event_bus=EventBus())

    assert summary.transitioned == 0
    assert summary.skipped_illegal == 1
    assert repository.load(brain.identity.id).applications[0].status is (ApplicationStatus.ACCEPTED)


def test_the_same_message_is_not_processed_twice(store, brain_with_application):
    """Sync runs on a schedule, so it sees the same inbox repeatedly. A message
    already acted on must not re-fire — and an idempotent second run is what
    proves it."""
    mailbox = FakeMailbox([_msg()])
    identity_id = brain_with_application.identity.id
    bus = EventBus()

    first = sync_replies(store, identity_id, mailbox, event_bus=bus)
    second = sync_replies(store, identity_id, mailbox, event_bus=bus)

    assert first.transitioned == 1
    assert second.transitioned == 0
    assert second.already_seen == 1


def test_sync_publishes_an_event_per_transition(store, brain_with_application):
    events: list = []
    bus = EventBus()
    bus.subscribe("application.status_changed", events.append)

    sync_replies(store, brain_with_application.identity.id, FakeMailbox([_msg()]), event_bus=bus)

    assert len(events) == 1
    assert events[0].payload["new_status"] == ApplicationStatus.INTERVIEWING.value


def test_summary_counts_everything_seen(store, brain_with_application):
    mailbox = FakeMailbox(
        [
            _msg(id="a", body="We'd like to invite you to an interview."),
            _msg(id="b", sender="x@nowhere.com", body="unrelated"),
            _msg(id="c", body="thanks for applying"),
        ]
    )
    summary = sync_replies(store, brain_with_application.identity.id, mailbox, event_bus=EventBus())
    assert summary.scanned == 3
    assert summary.transitioned == 1


# --- company matching precision (regression: substring false positives) ------


def test_a_company_name_is_not_matched_as_a_substring(store):
    """'On' must not match 'notion.com', and 'Meta' must not match
    'meta-analysis' — matching is on whole tokens, not substrings, or an
    unrelated recruiter email would advance the wrong application."""
    repository = CareerBrainRepository(store)
    brain = CareerBrain(identity=Identity(full_name="Sahil", email="sahil@example.com"))
    brain.applications.append(
        Application(job_title="Designer", company_name="On", status=ApplicationStatus.APPLIED)
    )
    repository.save(brain)

    mailbox = FakeMailbox(
        [
            _msg(
                id="x",
                sender="recruiting@notion.com",
                subject="Your Notion application",
                body="We'd like to invite you to an interview.",
            )
        ]
    )
    summary = sync_replies(store, brain.identity.id, mailbox, event_bus=EventBus())

    assert summary.transitioned == 0
    assert repository.load(brain.identity.id).applications[0].status is ApplicationStatus.APPLIED


def test_a_multiword_company_matches_when_all_tokens_are_present(store):
    repository = CareerBrainRepository(store)
    brain = CareerBrain(identity=Identity(full_name="Sahil", email="sahil@example.com"))
    brain.applications.append(
        Application(
            job_title="Engineer",
            company_name="Prop Solutions",
            status=ApplicationStatus.APPLIED,
        )
    )
    repository.save(brain)

    mailbox = FakeMailbox(
        [
            _msg(
                id="y",
                sender="hr@propsolutions.com",
                subject="Prop Solutions — interview invite",
                body="Let's schedule a call.",
            )
        ]
    )
    summary = sync_replies(store, brain.identity.id, mailbox, event_bus=EventBus())
    assert summary.transitioned == 1
