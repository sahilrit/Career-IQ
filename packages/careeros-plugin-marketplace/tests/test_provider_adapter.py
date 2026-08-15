"""Tests for ProviderPluginAdapter."""

from __future__ import annotations

from careeros_plugin_marketplace import ProviderPluginAdapter
from careeros_plugin_sdk import PluginManifest


def _manifest() -> PluginManifest:
    return PluginManifest(id="careeros-remoteok", name="RemoteOK", version="1.0.0")


def test_manifest_property_returns_the_given_manifest():
    adapter = ProviderPluginAdapter(_manifest())
    assert adapter.manifest.id == "careeros-remoteok"


def test_on_enable_calls_the_callback():
    calls = []
    adapter = ProviderPluginAdapter(_manifest(), on_enable=lambda: calls.append("enabled"))
    adapter.on_enable()
    assert calls == ["enabled"]


def test_on_disable_calls_the_callback():
    calls = []
    adapter = ProviderPluginAdapter(_manifest(), on_disable=lambda: calls.append("disabled"))
    adapter.on_disable()
    assert calls == ["disabled"]


def test_missing_callbacks_are_a_no_op():
    adapter = ProviderPluginAdapter(_manifest())
    adapter.on_enable()
    adapter.on_disable()
