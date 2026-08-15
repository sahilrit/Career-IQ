"""Tests for OnboardingProgress / OnboardingProgressRepository."""

from __future__ import annotations

from careeros_onboarding import OnboardingStep


def test_fresh_progress_has_no_current_step(progress_repository):
    progress = progress_repository.load("user-1")
    assert progress.current_step is None
    assert progress.next_step == OnboardingStep.SIGNUP
    assert progress.is_fully_onboarded is False


def test_marking_a_step_complete_updates_current_and_next(progress_repository):
    progress_repository.mark_complete("user-1", OnboardingStep.SIGNUP)
    progress = progress_repository.load("user-1")
    assert progress.current_step == OnboardingStep.SIGNUP
    assert progress.next_step == OnboardingStep.CAREER_BRAIN_SETUP


def test_current_step_is_the_furthest_reached_regardless_of_marking_order(progress_repository):
    progress_repository.mark_complete("user-1", OnboardingStep.CHOOSE_CAPABILITIES)
    progress_repository.mark_complete("user-1", OnboardingStep.SIGNUP)
    progress = progress_repository.load("user-1")
    assert progress.current_step == OnboardingStep.CHOOSE_CAPABILITIES


def test_marking_the_same_step_twice_does_not_duplicate(progress_repository):
    progress_repository.mark_complete("user-1", OnboardingStep.SIGNUP)
    progress_repository.mark_complete("user-1", OnboardingStep.SIGNUP)
    progress = progress_repository.load("user-1")
    assert progress.completed_steps.count(OnboardingStep.SIGNUP) == 1


def test_final_step_has_no_next_step_and_is_fully_onboarded(progress_repository):
    progress_repository.mark_complete("user-1", OnboardingStep.START)
    progress = progress_repository.load("user-1")
    assert progress.next_step is None
    assert progress.is_fully_onboarded is True


def test_progress_is_isolated_per_user(progress_repository):
    progress_repository.mark_complete("user-1", OnboardingStep.SIGNUP)
    other = progress_repository.load("user-2")
    assert other.current_step is None
