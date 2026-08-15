"""careeros_compliance exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class ComplianceError(CareerOSError):
    """Base class for all compliance errors."""
