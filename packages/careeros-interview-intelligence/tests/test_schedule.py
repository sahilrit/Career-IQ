"""Tests for due_milestones."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from careeros_calendar_assistant import CalendarEvent, InterviewDetails, build_calendar_event
from careeros_interview_intelligence import BriefingMilestone, due_milestones

_INTERVIEW_AT = datetime(2026, 1, 10, 14, 0, tzinfo=UTC)


def _event() -> CalendarEvent:
    details = InterviewDetails(scheduled_at=_INTERVIEW_AT)
    return build_calendar_event("Interview", details)


def test_no_milestones_due_far_before_the_interview():
    now = _INTERVIEW_AT - timedelta(hours=72)
    assert due_milestones(_event(), now=now, already_fired=set()) == []


def test_48h_milestone_is_due_at_the_48h_mark():
    now = _INTERVIEW_AT - timedelta(hours=48)
    assert due_milestones(_event(), now=now, already_fired=set()) == [BriefingMilestone.H48]


def test_48h_and_24h_are_both_due_once_within_24h():
    now = _INTERVIEW_AT - timedelta(hours=23)
    result = due_milestones(_event(), now=now, already_fired=set())
    assert result == [BriefingMilestone.H48, BriefingMilestone.H24]


def test_all_three_milestones_due_just_before_the_interview():
    now = _INTERVIEW_AT - timedelta(hours=1)
    result = due_milestones(_event(), now=now, already_fired=set())
    assert result == [BriefingMilestone.H48, BriefingMilestone.H24, BriefingMilestone.H2]


def test_already_fired_milestones_are_excluded():
    now = _INTERVIEW_AT - timedelta(hours=1)
    result = due_milestones(_event(), now=now, already_fired={BriefingMilestone.H48})
    assert result == [BriefingMilestone.H24, BriefingMilestone.H2]


def test_no_scheduled_at_means_nothing_is_ever_due():
    event = build_calendar_event("Interview", InterviewDetails(scheduled_at=None))
    assert due_milestones(event, now=datetime.now(UTC), already_fired=set()) == []
