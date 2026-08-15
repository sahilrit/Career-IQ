"""Per-plugin health reporting, built on Phase 23's PlatformHealthMonitor
rather than a new health mechanism — a plugin is healthy exactly when
its registry state is ENABLED; anything else is reported degraded with
the actual state as the detail, no deeper introspection attempted since
that would mean executing arbitrary plugin code.
"""

from __future__ import annotations

from careeros_core import ComponentHealth, ComponentStatus, PlatformHealthMonitor
from careeros_plugin_sdk import PluginRegistry, PluginState


def _check_plugin_health(registry: PluginRegistry, plugin_id: str) -> ComponentHealth:
    state = registry.state_of(plugin_id)
    if state == PluginState.ENABLED:
        return ComponentHealth(name=plugin_id, status=ComponentStatus.HEALTHY)
    return ComponentHealth(
        name=plugin_id, status=ComponentStatus.DEGRADED, detail=f"state={state.value}"
    )


def register_plugin_health_checks(monitor: PlatformHealthMonitor, registry: PluginRegistry) -> None:
    for plugin in registry.list_all():
        plugin_id = plugin.manifest.id
        monitor.register_check(
            plugin_id, lambda plugin_id=plugin_id: _check_plugin_health(registry, plugin_id)
        )
