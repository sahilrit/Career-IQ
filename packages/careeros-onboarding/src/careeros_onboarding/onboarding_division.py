"""OnboardingDivision: the facade tying progress tracking and step
guidance together — each user's own path to "each user gets their own
AI career agency."
"""

from __future__ import annotations

from careeros_onboarding.onboarding_step import (
    OnboardingProgress,
    OnboardingProgressRepository,
    OnboardingStep,
)
from careeros_onboarding.step_descriptions import STEP_DESCRIPTIONS


class OnboardingDivision:
    def __init__(self, progress_repository: OnboardingProgressRepository) -> None:
        self._progress = progress_repository

    def progress_for(self, user_id: str) -> OnboardingProgress:
        return self._progress.load(user_id)

    def mark_complete(self, user_id: str, step: OnboardingStep) -> OnboardingProgress:
        return self._progress.mark_complete(user_id, step)

    def next_step_description(self, user_id: str) -> str | None:
        next_step = self._progress.load(user_id).next_step
        if next_step is None:
            return None
        return STEP_DESCRIPTIONS[next_step]

    def is_fully_onboarded(self, user_id: str) -> bool:
        return self._progress.load(user_id).is_fully_onboarded
