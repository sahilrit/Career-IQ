"""careeros_plugin_marketplace: the Plugin Marketplace.

A browsable catalog on top of Phase 3's PluginRegistry, an adapter for
wrapping existing providers as installable plugins, and per-plugin
health reporting built on Phase 23's PlatformHealthMonitor.
"""

from careeros_plugin_marketplace.catalog import CatalogListing, PluginCategory
from careeros_plugin_marketplace.exceptions import (
    ListingNotFoundError,
    ListingNotInstallableError,
    PluginMarketplaceError,
)
from careeros_plugin_marketplace.health import register_plugin_health_checks
from careeros_plugin_marketplace.marketplace import PluginMarketplace
from careeros_plugin_marketplace.provider_adapter import ProviderPluginAdapter
from careeros_plugin_marketplace.seed_catalog import SEED_CATALOG

__all__ = [
    "SEED_CATALOG",
    "CatalogListing",
    "ListingNotFoundError",
    "ListingNotInstallableError",
    "PluginCategory",
    "PluginMarketplace",
    "PluginMarketplaceError",
    "ProviderPluginAdapter",
    "register_plugin_health_checks",
]
