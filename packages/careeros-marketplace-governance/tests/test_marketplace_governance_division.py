"""Tests for the MarketplaceGovernanceDivision facade."""

from __future__ import annotations

from careeros_marketplace_governance import MarketplaceGovernanceDivision
from careeros_plugin_sdk import PluginManifest


def test_review_delegates_to_run_governance_review(store, manifest):
    division = MarketplaceGovernanceDivision(store)
    report = division.review(manifest, build_fn=lambda: object())
    assert report.plugin_id == "careeros-example"
    assert report.passed is True


def test_review_applies_configured_permission_policy(store):
    division = MarketplaceGovernanceDivision(
        store, dangerous_permissions=frozenset({"delete_all_data"})
    )
    manifest = PluginManifest(
        id="p",
        name="P",
        version="1.0.0",
        description="x",
        actions=["a"],
        permissions=["delete_all_data"],
    )
    report = division.review(manifest, build_fn=lambda: object())
    assert report.passed is False


def test_version_lifecycle(store):
    division = MarketplaceGovernanceDivision(store)
    division.publish_version("careeros-example", "1.0.0")
    division.publish_version("careeros-example", "2.0.0")
    assert division.current_version("careeros-example") == "2.0.0"
    division.rollback_to("careeros-example", "1.0.0")
    assert division.current_version("careeros-example") == "1.0.0"
    assert len(division.version_history("careeros-example")) == 2
