"""Tests for the PluginMarketplace facade."""

from __future__ import annotations

import pytest

from careeros_core import ComponentStatus
from careeros_plugin_marketplace import (
    ListingNotFoundError,
    ListingNotInstallableError,
    PluginCategory,
    PluginMarketplace,
)


def test_list_catalog_returns_everything_with_no_filter(catalog):
    marketplace = PluginMarketplace(catalog)
    assert len(marketplace.list_catalog()) == len(catalog)


def test_list_catalog_filters_by_category(catalog):
    marketplace = PluginMarketplace(catalog)
    job_boards = marketplace.list_catalog(category=PluginCategory.JOB_BOARD)
    assert all(listing.category == PluginCategory.JOB_BOARD for listing in job_boards)
    assert any(listing.manifest.id == "careeros-remoteok" for listing in job_boards)


def test_search_matches_name_case_insensitively(catalog):
    marketplace = PluginMarketplace(catalog)
    results = marketplace.search("remoteok")
    assert any(listing.manifest.id == "careeros-remoteok" for listing in results)


def test_search_matches_description(catalog):
    marketplace = PluginMarketplace(catalog)
    results = marketplace.search("browser automation")
    assert any(listing.manifest.id == "careeros-fiverr" for listing in results)


def test_install_registers_and_enables_an_installable_listing(catalog):
    marketplace = PluginMarketplace(catalog)
    plugin = marketplace.install("careeros-remoteok")
    assert plugin.manifest.id == "careeros-remoteok"
    assert marketplace.installed_plugins() == [plugin]


def test_install_raises_for_a_catalog_only_listing(catalog):
    marketplace = PluginMarketplace(catalog)
    with pytest.raises(ListingNotInstallableError):
        marketplace.install("careeros-linkedin")


def test_install_raises_for_an_unknown_id(catalog):
    marketplace = PluginMarketplace(catalog)
    with pytest.raises(ListingNotFoundError):
        marketplace.install("not-a-real-plugin")


def test_uninstall_removes_from_installed_plugins(catalog):
    marketplace = PluginMarketplace(catalog)
    marketplace.install("careeros-remoteok")
    marketplace.uninstall("careeros-remoteok")
    assert marketplace.installed_plugins() == []


def test_health_report_reflects_installed_plugin_state(catalog):
    marketplace = PluginMarketplace(catalog)
    marketplace.install("careeros-remoteok")
    report = marketplace.health_report()
    assert report.overall_status == ComponentStatus.HEALTHY
