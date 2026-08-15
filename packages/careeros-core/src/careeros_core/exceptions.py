"""careeros_core exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class CoreError(CareerOSError):
    """Base class for all careeros_core errors."""


class ContractViolationError(CoreError):
    """Raised when an event's payload doesn't match its registered contract."""
