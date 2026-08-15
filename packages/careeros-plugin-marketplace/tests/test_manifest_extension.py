"""Tests for the new PluginManifest fields (Phase 48's additions to Phase 3)."""

from __future__ import annotations

from careeros_plugin_sdk import PluginManifest


def test_new_fields_default_to_empty():
    manifest = PluginManifest(id="plugin", name="x", version="1.0.0")
    assert manifest.triggers == []
    assert manifest.actions == []
    assert manifest.tools == []
    assert manifest.workflows == []
    assert manifest.health_check_action is None


def test_new_fields_can_be_set():
    manifest = PluginManifest(
        id="plugin",
        name="x",
        version="1.0.0",
        triggers=["job.scored"],
        actions=["discover_jobs"],
        tools=["search_jobs"],
        workflows=["default_apply_workflow"],
        health_check_action="discover_jobs",
    )
    assert manifest.triggers == ["job.scored"]
    assert manifest.health_check_action == "discover_jobs"
