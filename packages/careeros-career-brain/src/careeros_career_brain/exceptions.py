"""Career Brain-specific exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class CareerBrainError(CareerOSError):
    """Base class for all Career Brain errors."""


class InvalidStatusTransitionError(CareerBrainError):
    """Raised when an Application status change violates the allowed workflow."""
