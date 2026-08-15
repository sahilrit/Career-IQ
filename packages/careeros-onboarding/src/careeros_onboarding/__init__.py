"""careeros_onboarding: Multi-User Production SaaS onboarding.

Tracks each user's real progress through:

    Signup -> Career Brain setup -> Connect accounts
      -> Choose capabilities -> Configure autonomy -> Start CareerOS

Each user gets their own AI career agency. This package only tracks
the journey — Phase 2/21/24/25/26 already do the real work of each step.
"""

from careeros_onboarding.exceptions import OnboardingError
from careeros_onboarding.onboarding_division import OnboardingDivision
from careeros_onboarding.onboarding_step import (
    OnboardingProgress,
    OnboardingProgressRepository,
    OnboardingStep,
)
from careeros_onboarding.step_descriptions import STEP_DESCRIPTIONS

__all__ = [
    "STEP_DESCRIPTIONS",
    "OnboardingDivision",
    "OnboardingError",
    "OnboardingProgress",
    "OnboardingProgressRepository",
    "OnboardingStep",
]
