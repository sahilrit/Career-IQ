"""Tests for the deterministic recruiter-email classifier.

The classifier reads one email and decides whether it signals an
interview, a rejection, an offer, or nothing actionable. It is
deliberately conservative: a message it isn't sure about produces no
transition, because a wrong automatic status change is worse than none.
"""

from __future__ import annotations

import pytest

from careeros_career_brain import ApplicationStatus
from careeros_reply_tracking.classifier import ReplySignal, classify_email


@pytest.mark.parametrize(
    "body",
    [
        "We'd like to invite you to an interview next week.",
        "Are you available for a call to discuss the role further?",
        "The hiring team would like to schedule a first-round interview.",
        "Congratulations — we'd love to move you to the next stage.",
    ],
)
def test_interview_language_signals_interviewing(body):
    signal = classify_email(subject="Your application", body=body)
    assert signal.target is ApplicationStatus.INTERVIEWING


@pytest.mark.parametrize(
    "body",
    [
        "Unfortunately, we won't be progressing your application.",
        "We have decided to move forward with other candidates.",
        "After careful consideration, we regret to inform you that you were not selected.",
        "We won't be taking your application further at this time.",
    ],
)
def test_rejection_language_signals_rejected(body):
    signal = classify_email(subject="Update on your application", body=body)
    assert signal.target is ApplicationStatus.REJECTED


@pytest.mark.parametrize(
    "body",
    [
        "We're delighted to offer you the position.",
        "Please find attached your formal offer of employment.",
        "We would like to extend an offer for the role.",
    ],
)
def test_offer_language_signals_offer(body):
    signal = classify_email(subject="Offer", body=body)
    assert signal.target is ApplicationStatus.OFFER


@pytest.mark.parametrize(
    "body",
    [
        "Thanks for applying! We've received your application.",
        "This is an automated confirmation that your application was submitted.",
        "Here is our monthly newsletter about life at Acme.",
        "",
    ],
)
def test_neutral_messages_signal_nothing(body):
    signal = classify_email(subject="Received", body=body)
    assert signal.target is None


def test_a_rejection_beats_an_interview_mention():
    """Rejections often quote the earlier interview: 'following your
    interview, we won't be progressing'. The negative outcome wins."""
    body = "Thank you for taking the time to interview. Unfortunately we won't be progressing."
    assert classify_email(subject="", body=body).target is ApplicationStatus.REJECTED


def test_an_offer_beats_an_interview_mention():
    body = "Following your interviews, we're delighted to offer you the position."
    assert classify_email(subject="", body=body).target is ApplicationStatus.OFFER


def test_the_signal_carries_the_matched_phrase_for_the_audit_trail():
    signal = classify_email(subject="", body="We'd like to invite you to interview.")
    assert signal.target is ApplicationStatus.INTERVIEWING
    assert signal.evidence
    assert signal.evidence.lower() in "we'd like to invite you to interview."


def test_classification_is_case_insensitive():
    assert (
        classify_email(subject="", body="UNFORTUNATELY WE WON'T BE PROGRESSING").target
        is ApplicationStatus.REJECTED
    )


def test_a_signal_with_no_target_is_falsy():
    assert not ReplySignal(target=None, evidence="")
    assert ReplySignal(target=ApplicationStatus.REJECTED, evidence="x")
