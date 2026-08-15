"""Observability & Reliability exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class ObservabilityError(CareerOSError):
    """Base class for all observability errors."""
