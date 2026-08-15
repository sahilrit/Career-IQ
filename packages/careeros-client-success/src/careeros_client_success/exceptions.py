"""Client Success Division exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class ClientSuccessError(CareerOSError):
    """Base class for all client success errors."""
