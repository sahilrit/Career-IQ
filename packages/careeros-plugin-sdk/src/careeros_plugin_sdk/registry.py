"""Plugin registry: validation, dependency resolution, and lifecycle.

This is the only thing in CareerOS that is allowed to call a plugin's
``on_enable``/``on_disable`` hooks, so enable/disable ordering and
dependency checks live in one place instead of every call site
reimplementing them.
"""

from __future__ import annotations

from careeros_common import get_logger
from careeros_plugin_sdk.exceptions import (
    DuplicatePluginError,
    PluginDependencyError,
    PluginNotFoundError,
)
from careeros_plugin_sdk.manifest import PluginManifest
from careeros_plugin_sdk.plugin import Plugin, PluginState
from careeros_plugin_sdk.versioning import satisfies

logger = get_logger(__name__)


class PluginRegistry:
    """Tracks installed plugins and manages their dependency-aware lifecycle."""

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}
        self._states: dict[str, PluginState] = {}

    def register(self, plugin: Plugin) -> None:
        manifest = plugin.manifest
        if manifest.id in self._plugins:
            raise DuplicatePluginError(f"Plugin {manifest.id!r} is already registered")
        self._validate_dependencies(manifest)
        self._plugins[manifest.id] = plugin
        self._states[manifest.id] = PluginState.REGISTERED
        logger.info("Registered plugin %s@%s", manifest.id, manifest.version)

    def unregister(self, plugin_id: str) -> None:
        self._require(plugin_id)
        dependents = [
            pid for pid, p in self._plugins.items() if plugin_id in p.manifest.dependencies
        ]
        if dependents:
            raise PluginDependencyError(
                f"Cannot remove {plugin_id!r}: still required by {dependents}"
            )
        if self._states[plugin_id] == PluginState.ENABLED:
            self.disable(plugin_id)
        del self._plugins[plugin_id]
        del self._states[plugin_id]
        logger.info("Unregistered plugin %s", plugin_id)

    def enable(self, plugin_id: str) -> None:
        plugin = self._require(plugin_id)
        for dep_id in plugin.manifest.dependencies:
            if self._states.get(dep_id) != PluginState.ENABLED:
                raise PluginDependencyError(
                    f"Cannot enable {plugin_id!r}: dependency {dep_id!r} is not enabled"
                )
        if self._states[plugin_id] != PluginState.ENABLED:
            plugin.on_enable()
            self._states[plugin_id] = PluginState.ENABLED
            logger.info("Enabled plugin %s", plugin_id)

    def disable(self, plugin_id: str) -> None:
        plugin = self._require(plugin_id)
        dependents = [
            pid
            for pid, p in self._plugins.items()
            if plugin_id in p.manifest.dependencies and self._states[pid] == PluginState.ENABLED
        ]
        if dependents:
            raise PluginDependencyError(
                f"Cannot disable {plugin_id!r}: still required by enabled plugins {dependents}"
            )
        if self._states[plugin_id] == PluginState.ENABLED:
            plugin.on_disable()
        self._states[plugin_id] = PluginState.DISABLED
        logger.info("Disabled plugin %s", plugin_id)

    def state_of(self, plugin_id: str) -> PluginState:
        self._require(plugin_id)
        return self._states[plugin_id]

    def get(self, plugin_id: str) -> Plugin:
        return self._require(plugin_id)

    def find_by_capability(self, capability: str) -> list[Plugin]:
        """Enabled plugins that declare ``capability`` in their manifest."""
        return [
            plugin
            for plugin_id, plugin in self._plugins.items()
            if capability in plugin.manifest.capabilities
            and self._states[plugin_id] == PluginState.ENABLED
        ]

    def list_all(self) -> list[Plugin]:
        return list(self._plugins.values())

    def _validate_dependencies(self, manifest: PluginManifest) -> None:
        for dep_id, constraint in manifest.dependencies.items():
            dep = self._plugins.get(dep_id)
            if dep is None:
                raise PluginDependencyError(
                    f"Plugin {manifest.id!r} depends on {dep_id!r}, which is not registered"
                )
            if not satisfies(dep.manifest.version, constraint):
                raise PluginDependencyError(
                    f"Plugin {manifest.id!r} requires {dep_id!r}{constraint}, but "
                    f"{dep_id!r}@{dep.manifest.version} is registered"
                )

    def _require(self, plugin_id: str) -> Plugin:
        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            raise PluginNotFoundError(f"No plugin registered with id {plugin_id!r}")
        return plugin
