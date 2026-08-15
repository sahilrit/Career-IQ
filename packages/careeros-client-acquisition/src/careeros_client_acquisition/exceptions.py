"""Client Acquisition Division exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class ClientAcquisitionError(CareerOSError):
    """Base class for all client acquisition errors."""
