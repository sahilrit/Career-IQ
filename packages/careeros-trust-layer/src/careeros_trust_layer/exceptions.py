"""Security & Trust Layer exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class TrustLayerError(CareerOSError):
    """Base class for all trust layer errors."""
