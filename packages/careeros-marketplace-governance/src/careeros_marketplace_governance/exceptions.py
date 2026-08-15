"""Marketplace Governance exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class MarketplaceGovernanceError(CareerOSError):
    """Base class for all marketplace governance errors."""


class VersionNotFoundError(MarketplaceGovernanceError):
    """Raised when rolling back to a version that was never published."""
