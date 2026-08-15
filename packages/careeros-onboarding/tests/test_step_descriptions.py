"""Tests for STEP_DESCRIPTIONS."""

from __future__ import annotations

from careeros_onboarding import STEP_DESCRIPTIONS, OnboardingStep


def test_every_step_has_a_description():
    assert set(STEP_DESCRIPTIONS) == set(OnboardingStep)


def test_every_description_is_non_empty():
    assert all(description.strip() for description in STEP_DESCRIPTIONS.values())
