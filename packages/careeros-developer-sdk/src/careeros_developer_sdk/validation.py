"""Manifest validation: fast, offline feedback for a plugin developer —
catches obvious authoring mistakes before the manifest ever reaches
PluginRegistry.register(), which only checks dependency satisfaction,
not authoring quality.
"""

from __future__ import annotations

from careeros_plugin_sdk import PluginManifest


def validate_plugin_manifest(manifest: PluginManifest) -> list[str]:
    issues: list[str] = []

    if not manifest.description:
        issues.append("description is empty")

    if not manifest.capabilities and not manifest.actions and not manifest.tools:
        issues.append("plugin declares no capabilities, actions, or tools")

    if manifest.health_check_action and manifest.health_check_action not in manifest.actions:
        issues.append(
            f"health_check_action {manifest.health_check_action!r} is not one of the "
            "declared actions"
        )

    if manifest.id in manifest.dependencies:
        issues.append(f"plugin {manifest.id!r} cannot depend on itself")

    return issues


def is_valid(manifest: PluginManifest) -> bool:
    return not validate_plugin_manifest(manifest)
