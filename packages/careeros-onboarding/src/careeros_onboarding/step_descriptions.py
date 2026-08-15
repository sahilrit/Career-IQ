"""Human-readable guidance for each onboarding step — what a UI shows
the user for "here's what's next."
"""

from __future__ import annotations

from careeros_onboarding.onboarding_step import OnboardingStep

STEP_DESCRIPTIONS: dict[OnboardingStep, str] = {
    OnboardingStep.SIGNUP: "Create your account.",
    OnboardingStep.CAREER_BRAIN_SETUP: (
        "Set up your Career Brain — identity, experience, skills, and goals."
    ),
    OnboardingStep.CONNECT_ACCOUNTS: (
        "Connect the accounts CareerOS should use (email, calendar, job boards)."
    ),
    OnboardingStep.CHOOSE_CAPABILITIES: (
        "Choose which capabilities to enable (job discovery, freelance acquisition, ...)."
    ),
    OnboardingStep.CONFIGURE_AUTONOMY: (
        "Configure how autonomously CareerOS should act on your behalf."
    ),
    OnboardingStep.START: "Start CareerOS.",
}
