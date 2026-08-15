"""Multi-User Production SaaS / Onboarding exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class OnboardingError(CareerOSError):
    """Base class for all onboarding errors."""
