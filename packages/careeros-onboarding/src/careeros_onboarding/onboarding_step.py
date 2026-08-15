"""OnboardingProgress: tracks how far one user has moved through the
roadmap's exact sequence:

    Signup -> Career Brain setup -> Connect accounts
      -> Choose capabilities -> Configure autonomy -> Start CareerOS

Same furthest-reached pattern as Phase 30/31/34/38's pipeline progress.
``user_id`` is meant to share Phase 25's tenancy User.id — this package
only tracks the journey, it doesn't perform any step itself (creating
the User, the Career Brain, connecting OAuth, choosing capabilities,
and configuring autonomy are Phase 2/21/24/25/26's real logic); the
caller marks a step complete only after actually doing it.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "onboarding_progress"


class OnboardingStep(StrEnum):
    SIGNUP = "signup"
    CAREER_BRAIN_SETUP = "career_brain_setup"
    CONNECT_ACCOUNTS = "connect_accounts"
    CHOOSE_CAPABILITIES = "choose_capabilities"
    CONFIGURE_AUTONOMY = "configure_autonomy"
    START = "start"


_STEP_ORDER = list(OnboardingStep)


class OnboardingProgress(BaseModel):
    user_id: str
    completed_steps: list[OnboardingStep] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def current_step(self) -> OnboardingStep | None:
        completed_set = set(self.completed_steps)
        current = None
        for step in _STEP_ORDER:
            if step in completed_set:
                current = step
        return current

    @property
    def next_step(self) -> OnboardingStep | None:
        current = self.current_step
        if current is None:
            return _STEP_ORDER[0]
        index = _STEP_ORDER.index(current)
        if index + 1 >= len(_STEP_ORDER):
            return None
        return _STEP_ORDER[index + 1]

    @property
    def is_fully_onboarded(self) -> bool:
        return self.next_step is None


class OnboardingProgressRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def load(self, user_id: str) -> OnboardingProgress:
        data = self._store.get_or_none(_ENTITY_TYPE, user_id)
        if data is None:
            return OnboardingProgress(user_id=user_id)
        return OnboardingProgress.model_validate(data)

    def mark_complete(self, user_id: str, step: OnboardingStep) -> OnboardingProgress:
        progress = self.load(user_id)
        if step not in progress.completed_steps:
            progress.completed_steps.append(step)
        progress.updated_at = datetime.now(UTC)
        self._store.put(_ENTITY_TYPE, user_id, progress.model_dump(mode="json"))
        return progress
