"""Zero-Cost Infrastructure Mode exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class ZeroCostModeError(CareerOSError):
    """Base class for all zero-cost mode errors."""


class ZeroCostViolationError(ZeroCostModeError):
    """Raised when a required capability has no free provider path."""
