"""careeros_developer_sdk: the official CareerOS Developer SDK.

Build a plugin — capabilities, permissions, triggers, actions, tools,
workflows, settings, dependencies, and a health check — with a fluent
builder instead of hand-writing a PluginManifest or subclassing Plugin
directly, and without modifying CareerOS Core.
"""

from careeros_developer_sdk.exceptions import DeveloperSdkError, UnknownActionError
from careeros_developer_sdk.plugin_builder import PluginBuilder
from careeros_developer_sdk.scaffold import generate_plugin_scaffold
from careeros_developer_sdk.simple_plugin import SimplePlugin
from careeros_developer_sdk.validation import is_valid, validate_plugin_manifest

__all__ = [
    "DeveloperSdkError",
    "PluginBuilder",
    "SimplePlugin",
    "UnknownActionError",
    "generate_plugin_scaffold",
    "is_valid",
    "validate_plugin_manifest",
]
