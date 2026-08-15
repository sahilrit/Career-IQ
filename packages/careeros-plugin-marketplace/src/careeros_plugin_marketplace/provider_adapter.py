"""ProviderPluginAdapter: wraps an existing capability (RemoteOK's
JobProvider registration, Fiverr's GigProvider registration, ...) as a
Phase 3 Plugin, so real, already-shipped providers can be listed and
installed through the unified marketplace without rewriting those
provider packages or forcing them onto the Plugin ABC directly.
"""

from __future__ import annotations

from collections.abc import Callable

from careeros_plugin_sdk import Plugin, PluginManifest


class ProviderPluginAdapter(Plugin):
    def __init__(
        self,
        manifest: PluginManifest,
        *,
        on_enable: Callable[[], None] | None = None,
        on_disable: Callable[[], None] | None = None,
    ) -> None:
        self._manifest = manifest
        self._on_enable = on_enable
        self._on_disable = on_disable

    @property
    def manifest(self) -> PluginManifest:
        return self._manifest

    def on_enable(self) -> None:
        if self._on_enable is not None:
            self._on_enable()

    def on_disable(self) -> None:
        if self._on_disable is not None:
            self._on_disable()
