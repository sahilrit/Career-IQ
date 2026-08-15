"""PluginMarketplace: the facade wrapping Phase 3's PluginRegistry with
a browsable catalog, search, install/uninstall, and health reporting.
"""

from __future__ import annotations

from careeros_core import PlatformHealthMonitor, PlatformHealthReport
from careeros_plugin_marketplace.catalog import CatalogListing, PluginCategory
from careeros_plugin_marketplace.exceptions import (
    ListingNotFoundError,
    ListingNotInstallableError,
)
from careeros_plugin_marketplace.health import register_plugin_health_checks
from careeros_plugin_marketplace.provider_adapter import ProviderPluginAdapter
from careeros_plugin_sdk import Plugin, PluginRegistry


class PluginMarketplace:
    def __init__(
        self, catalog: list[CatalogListing], *, registry: PluginRegistry | None = None
    ) -> None:
        self._catalog = list(catalog)
        self._registry = registry or PluginRegistry()

    def list_catalog(self, *, category: PluginCategory | None = None) -> list[CatalogListing]:
        if category is None:
            return list(self._catalog)
        return [listing for listing in self._catalog if listing.category == category]

    def search(self, query: str) -> list[CatalogListing]:
        lowered = query.lower()
        return [
            listing
            for listing in self._catalog
            if lowered in listing.manifest.name.lower()
            or lowered in listing.manifest.description.lower()
        ]

    def install(self, plugin_id: str) -> Plugin:
        listing = self._require_listing(plugin_id)
        if not listing.is_installable:
            raise ListingNotInstallableError(f"{plugin_id!r} has no working implementation yet")
        adapter = ProviderPluginAdapter(listing.manifest)
        self._registry.register(adapter)
        self._registry.enable(plugin_id)
        return adapter

    def uninstall(self, plugin_id: str) -> None:
        self._registry.unregister(plugin_id)

    def installed_plugins(self) -> list[Plugin]:
        return self._registry.list_all()

    def health_report(self) -> PlatformHealthReport:
        monitor = PlatformHealthMonitor()
        register_plugin_health_checks(monitor, self._registry)
        return monitor.run()

    def _require_listing(self, plugin_id: str) -> CatalogListing:
        for listing in self._catalog:
            if listing.manifest.id == plugin_id:
                return listing
        raise ListingNotFoundError(f"No catalog listing for {plugin_id!r}")
