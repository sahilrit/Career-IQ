"""Tests for interview stage detection."""

from __future__ import annotations

from careeros_calendar_assistant import InterviewStage, detect_stage


def test_onsite_final_round():
    assert detect_stage("Final round: onsite interview") == InterviewStage.ONSITE_FINAL


def test_technical_interview():
    assert detect_stage("Technical interview next week") == InterviewStage.TECHNICAL


def test_phone_screen():
    assert detect_stage("Initial phone screen with our recruiter") == InterviewStage.PHONE_SCREEN


def test_generic_interview_mention_falls_back_to_general():
    assert detect_stage("Let's set up an interview") == InterviewStage.GENERAL


def test_no_interview_signal_is_unknown():
    assert detect_stage("Thanks for your application") == InterviewStage.UNKNOWN
