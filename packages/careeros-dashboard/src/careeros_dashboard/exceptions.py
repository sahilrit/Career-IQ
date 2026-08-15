"""Dashboard exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class DashboardError(CareerOSError):
    """Base class for all dashboard errors."""
