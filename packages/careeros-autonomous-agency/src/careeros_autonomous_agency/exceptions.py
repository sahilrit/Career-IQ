"""careeros_autonomous_agency exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class AutonomousAgencyError(CareerOSError):
    """Base class for all autonomous-agency errors."""


class CycleNotCompleteError(AutonomousAgencyError):
    """Raised when starting a new cycle before every stage has been reached."""
