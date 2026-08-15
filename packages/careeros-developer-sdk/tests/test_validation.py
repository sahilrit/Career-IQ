"""Tests for validate_plugin_manifest / is_valid."""

from __future__ import annotations

from careeros_developer_sdk import is_valid, validate_plugin_manifest
from careeros_plugin_sdk import PluginManifest


def test_empty_description_is_flagged():
    manifest = PluginManifest(id="p", name="P", version="1.0.0", capabilities=["FIND_JOBS"])
    assert "description is empty" in validate_plugin_manifest(manifest)


def test_no_capabilities_actions_or_tools_is_flagged():
    manifest = PluginManifest(id="p", name="P", version="1.0.0", description="Does things.")
    issues = validate_plugin_manifest(manifest)
    assert any("no capabilities, actions, or tools" in issue for issue in issues)


def test_health_check_action_not_in_actions_is_flagged():
    manifest = PluginManifest(
        id="p",
        name="P",
        version="1.0.0",
        description="Does things.",
        actions=["discover_jobs"],
        health_check_action="apply",
    )
    issues = validate_plugin_manifest(manifest)
    assert any("health_check_action" in issue for issue in issues)


def test_self_dependency_is_flagged():
    manifest = PluginManifest(
        id="p",
        name="P",
        version="1.0.0",
        description="Does things.",
        actions=["a"],
        dependencies={"p": "^1.0.0"},
    )
    issues = validate_plugin_manifest(manifest)
    assert any("cannot depend on itself" in issue for issue in issues)


def test_well_formed_manifest_has_no_issues():
    manifest = PluginManifest(
        id="p",
        name="P",
        version="1.0.0",
        description="Does things.",
        actions=["discover_jobs"],
        health_check_action="discover_jobs",
    )
    assert validate_plugin_manifest(manifest) == []
    assert is_valid(manifest) is True


def test_is_valid_is_false_when_issues_exist():
    manifest = PluginManifest(id="p", name="P", version="1.0.0")
    assert is_valid(manifest) is False
