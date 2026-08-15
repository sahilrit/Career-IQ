"""careeros_plugin_sdk: the plugin interface, manifest schema, versioning,
and registry every CareerOS plugin is built and installed against.
"""

from careeros_plugin_sdk.exceptions import (
    DuplicatePluginError,
    PluginDependencyError,
    PluginError,
    PluginNotFoundError,
    PluginValidationError,
)
from careeros_plugin_sdk.manifest import PluginManifest
from careeros_plugin_sdk.plugin import Plugin, PluginState
from careeros_plugin_sdk.registry import PluginRegistry
from careeros_plugin_sdk.versioning import Version, satisfies

__all__ = [
    "DuplicatePluginError",
    "Plugin",
    "PluginDependencyError",
    "PluginError",
    "PluginManifest",
    "PluginNotFoundError",
    "PluginRegistry",
    "PluginState",
    "PluginValidationError",
    "Version",
    "satisfies",
]
