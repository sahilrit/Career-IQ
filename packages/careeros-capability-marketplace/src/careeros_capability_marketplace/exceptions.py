"""Capability marketplace exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class MarketplaceError(CareerOSError):
    """Base class for all capability marketplace errors."""


class NoProviderAvailableError(MarketplaceError):
    """Raised when no healthy provider is available for a requested capability."""
