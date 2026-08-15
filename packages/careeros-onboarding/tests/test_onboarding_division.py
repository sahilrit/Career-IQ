"""Tests for the OnboardingDivision facade."""

from __future__ import annotations

import pytest

from careeros_onboarding import OnboardingDivision, OnboardingStep


@pytest.fixture
def division(progress_repository):
    return OnboardingDivision(progress_repository)


def test_next_step_description_before_any_progress(division):
    description = division.next_step_description("user-1")
    assert "account" in description.lower()


def test_next_step_description_updates_as_steps_complete(division):
    division.mark_complete("user-1", OnboardingStep.SIGNUP)
    description = division.next_step_description("user-1")
    assert "career brain" in description.lower()


def test_next_step_description_is_none_once_fully_onboarded(division):
    for step in OnboardingStep:
        division.mark_complete("user-1", step)
    assert division.next_step_description("user-1") is None


def test_is_fully_onboarded_reflects_progress(division):
    assert division.is_fully_onboarded("user-1") is False
    for step in OnboardingStep:
        division.mark_complete("user-1", step)
    assert division.is_fully_onboarded("user-1") is True


def test_progress_for_delegates(division):
    division.mark_complete("user-1", OnboardingStep.SIGNUP)
    assert division.progress_for("user-1").current_step == OnboardingStep.SIGNUP
