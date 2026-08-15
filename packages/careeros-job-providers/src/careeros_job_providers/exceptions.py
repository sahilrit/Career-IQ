"""Job provider framework exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class JobProviderError(CareerOSError):
    """Base class for all job provider errors (network, parsing, etc.)."""
