"""PluginBuilder: a fluent API for declaring a plugin — capabilities,
permissions, triggers, actions, tools, workflows, settings,
dependencies, and a health check — without hand-writing a
PluginManifest or subclassing Plugin. ``actions`` is derived
automatically from whatever handlers get registered via ``.action()``,
so the manifest can never drift out of sync with what the plugin
actually implements.
"""

from __future__ import annotations

from collections.abc import Callable

from careeros_developer_sdk.simple_plugin import SimplePlugin
from careeros_plugin_sdk import PluginManifest


class PluginBuilder:
    def __init__(self, plugin_id: str, name: str, version: str) -> None:
        self._id = plugin_id
        self._name = name
        self._version = version
        self._description = ""
        self._capabilities: list[str] = []
        self._permissions: list[str] = []
        self._dependencies: dict[str, str] = {}
        self._settings_schema: dict[str, object] = {}
        self._triggers: list[str] = []
        self._tools: list[str] = []
        self._workflows: list[str] = []
        self._health_check_action: str | None = None
        self._action_handlers: dict[str, Callable[..., object]] = {}
        self._on_enable: Callable[[], None] | None = None
        self._on_disable: Callable[[], None] | None = None

    def description(self, text: str) -> PluginBuilder:
        self._description = text
        return self

    def capability(self, name: str) -> PluginBuilder:
        self._capabilities.append(name)
        return self

    def permission(self, name: str) -> PluginBuilder:
        self._permissions.append(name)
        return self

    def dependency(self, plugin_id: str, constraint: str) -> PluginBuilder:
        self._dependencies[plugin_id] = constraint
        return self

    def setting(self, key: str, schema: dict[str, object]) -> PluginBuilder:
        self._settings_schema[key] = schema
        return self

    def trigger(self, event_type: str) -> PluginBuilder:
        self._triggers.append(event_type)
        return self

    def tool(self, name: str) -> PluginBuilder:
        self._tools.append(name)
        return self

    def workflow(self, workflow_id: str) -> PluginBuilder:
        self._workflows.append(workflow_id)
        return self

    def action(self, name: str, handler: Callable[..., object]) -> PluginBuilder:
        self._action_handlers[name] = handler
        return self

    def health_check(self, action_name: str) -> PluginBuilder:
        self._health_check_action = action_name
        return self

    def on_enable(self, callback: Callable[[], None]) -> PluginBuilder:
        self._on_enable = callback
        return self

    def on_disable(self, callback: Callable[[], None]) -> PluginBuilder:
        self._on_disable = callback
        return self

    def build(self) -> SimplePlugin:
        manifest = PluginManifest(
            id=self._id,
            name=self._name,
            version=self._version,
            description=self._description,
            capabilities=self._capabilities,
            permissions=self._permissions,
            dependencies=self._dependencies,
            settings_schema=self._settings_schema,
            triggers=self._triggers,
            actions=list(self._action_handlers),
            tools=self._tools,
            workflows=self._workflows,
            health_check_action=self._health_check_action,
        )
        return SimplePlugin(
            manifest,
            self._action_handlers,
            on_enable=self._on_enable,
            on_disable=self._on_disable,
        )
