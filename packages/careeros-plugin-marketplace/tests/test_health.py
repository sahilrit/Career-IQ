"""Tests for register_plugin_health_checks."""

from __future__ import annotations

from careeros_core import ComponentStatus, PlatformHealthMonitor
from careeros_plugin_marketplace import ProviderPluginAdapter, register_plugin_health_checks
from careeros_plugin_sdk import PluginManifest, PluginRegistry


def test_enabled_plugin_reports_healthy():
    registry = PluginRegistry()
    registry.register(ProviderPluginAdapter(PluginManifest(id="a", name="A", version="1.0.0")))
    registry.enable("a")

    monitor = PlatformHealthMonitor()
    register_plugin_health_checks(monitor, registry)
    report = monitor.run()

    assert report.overall_status == ComponentStatus.HEALTHY


def test_registered_but_not_enabled_plugin_reports_degraded():
    registry = PluginRegistry()
    registry.register(ProviderPluginAdapter(PluginManifest(id="a", name="A", version="1.0.0")))

    monitor = PlatformHealthMonitor()
    register_plugin_health_checks(monitor, registry)
    report = monitor.run()

    assert report.overall_status == ComponentStatus.DEGRADED
    assert "registered" in report.components[0].detail
