"""Plugin Marketplace exceptions. All subclass CareerOSError."""

from __future__ import annotations

from careeros_common import CareerOSError


class PluginMarketplaceError(CareerOSError):
    """Base class for all plugin marketplace errors."""


class ListingNotInstallableError(PluginMarketplaceError):
    """Raised when trying to install a catalog-only (not yet implemented) listing."""


class ListingNotFoundError(PluginMarketplaceError):
    """Raised when a plugin id has no catalog listing at all."""
