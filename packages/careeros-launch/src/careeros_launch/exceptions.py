"""careeros_launch exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class LaunchError(CareerOSError):
    """Base class for all production-launch errors."""


class LaunchNotReadyError(LaunchError):
    """Raised when announcing a launch while the readiness gate fails."""
