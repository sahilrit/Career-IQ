"""careeros_beta exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class BetaError(CareerOSError):
    """Base class for all beta-release errors."""


class BetaCohortFullError(BetaError):
    """Raised when inviting past the beta cohort's seat capacity."""
