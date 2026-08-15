"""Tests for interview detail extraction from free email text."""

from __future__ import annotations

from careeros_calendar_assistant import InterviewStage, extract_interview_details


def test_extracts_a_full_datetime():
    details = extract_interview_details(
        "Interview scheduled",
        "Let's meet on January 12, 2026 at 2:00 PM EST for your technical interview.",
    )
    assert details.scheduled_at is not None
    assert details.scheduled_at.year == 2026
    assert details.scheduled_at.month == 1
    assert details.scheduled_at.day == 12
    assert details.scheduled_at.hour == 14


def test_extracts_timezone():
    details = extract_interview_details("Interview", "Meeting at 2:00 PM EST on Jan 12, 2026.")
    assert details.timezone == "America/New_York"


def test_extracts_zoom_platform_and_link():
    details = extract_interview_details(
        "Interview via Zoom",
        "Join here: https://zoom.us/j/123456789 on Jan 12, 2026 at 2pm.",
    )
    assert details.platform == "zoom"
    assert details.meeting_link == "https://zoom.us/j/123456789"


def test_extracts_google_meet_platform():
    details = extract_interview_details(
        "Interview", "Please join via https://meet.google.com/abc-defg-hij on Jan 12, 2026."
    )
    assert details.platform == "google_meet"


def test_detects_phone_platform_without_a_link():
    details = extract_interview_details(
        "Interview", "This will be a phone screen — we'll call you on Jan 12, 2026 at 2pm."
    )
    assert details.platform == "phone"
    assert details.meeting_link is None


def test_detects_onsite_platform():
    details = extract_interview_details(
        "Interview", "Please come onsite for your final round interview on Jan 12, 2026."
    )
    assert details.platform == "onsite"


def test_extracts_interviewer_names():
    details = extract_interview_details(
        "Interview", "You'll be meeting with Jane Smith, John Doe for the technical interview."
    )
    assert details.interviewers == ["Jane Smith", "John Doe"]


def test_stage_is_carried_through():
    details = extract_interview_details("Technical interview", "Coding interview on Jan 12.")
    assert details.stage == InterviewStage.TECHNICAL


def test_missing_fields_are_none_or_empty_not_errors():
    details = extract_interview_details("Hi there", "Thanks for reaching out.")
    assert details.platform is None
    assert details.meeting_link is None
    assert details.interviewers == []
