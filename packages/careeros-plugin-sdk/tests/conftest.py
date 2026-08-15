"""Shared fixtures for plugin SDK tests."""

from __future__ import annotations

import pytest

from careeros_plugin_sdk import Plugin, PluginManifest


class FakePlugin(Plugin):
    def __init__(self, manifest: PluginManifest) -> None:
        self._manifest = manifest
        self.enable_calls = 0
        self.disable_calls = 0

    @property
    def manifest(self) -> PluginManifest:
        return self._manifest

    def on_enable(self) -> None:
        self.enable_calls += 1

    def on_disable(self) -> None:
        self.disable_calls += 1


def make_plugin(
    plugin_id: str,
    version: str = "1.0.0",
    capabilities: list[str] | None = None,
    dependencies: dict[str, str] | None = None,
) -> FakePlugin:
    return FakePlugin(
        PluginManifest(
            id=plugin_id,
            name=plugin_id.title(),
            version=version,
            capabilities=capabilities or [],
            dependencies=dependencies or {},
        )
    )


@pytest.fixture
def make_fake_plugin():
    return make_plugin
