"""Career Intelligence Engine exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class CareerIntelligenceError(CareerOSError):
    """Base class for all career intelligence errors."""
