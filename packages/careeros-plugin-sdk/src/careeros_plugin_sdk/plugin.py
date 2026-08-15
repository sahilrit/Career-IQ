"""The runtime plugin interface every CareerOS plugin implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum

from careeros_plugin_sdk.manifest import PluginManifest


class PluginState(StrEnum):
    REGISTERED = "registered"
    ENABLED = "enabled"
    DISABLED = "disabled"


class Plugin(ABC):
    """Base class every CareerOS plugin subclasses.

    A plugin supplies its static ``manifest`` and optional lifecycle
    hooks; the ``PluginRegistry`` — not the plugin itself — decides when
    those hooks run, so enable/disable ordering and dependency checks stay
    centralized rather than every plugin re-implementing them.
    """

    @property
    @abstractmethod
    def manifest(self) -> PluginManifest: ...

    def on_enable(self) -> None:  # noqa: B027 - optional hook, not required on every plugin
        """Called once when the plugin transitions to ENABLED. Override as needed."""

    def on_disable(self) -> None:  # noqa: B027 - optional hook, not required on every plugin
        """Called once when the plugin transitions to DISABLED. Override as needed."""
