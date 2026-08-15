"""careeros_tenancy exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class TenancyError(CareerOSError):
    """Base class for all tenancy errors."""


class PermissionDeniedError(TenancyError):
    """Raised when a role lacks the required permission for an action."""
