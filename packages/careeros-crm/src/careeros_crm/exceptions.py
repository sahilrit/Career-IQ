"""CRM & Relationship Intelligence exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class CrmError(CareerOSError):
    """Base class for all CRM errors."""
