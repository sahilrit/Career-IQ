"""Tests for PlatformHealthMonitor."""

from __future__ import annotations

from careeros_core import ComponentHealth, ComponentStatus, PlatformHealthMonitor


def test_no_checks_registered_is_healthy_by_default():
    monitor = PlatformHealthMonitor()
    report = monitor.run()
    assert report.overall_status == ComponentStatus.HEALTHY
    assert report.components == []


def test_all_healthy_checks_yield_healthy_overall():
    monitor = PlatformHealthMonitor()
    monitor.register_check("runtime", lambda: ComponentHealth("runtime", ComponentStatus.HEALTHY))
    monitor.register_check("browser", lambda: ComponentHealth("browser", ComponentStatus.HEALTHY))
    assert monitor.run().overall_status == ComponentStatus.HEALTHY


def test_one_down_component_makes_overall_down():
    monitor = PlatformHealthMonitor()
    monitor.register_check("runtime", lambda: ComponentHealth("runtime", ComponentStatus.HEALTHY))
    monitor.register_check("browser", lambda: ComponentHealth("browser", ComponentStatus.DOWN))
    assert monitor.run().overall_status == ComponentStatus.DOWN


def test_degraded_without_down_makes_overall_degraded():
    monitor = PlatformHealthMonitor()
    monitor.register_check("runtime", lambda: ComponentHealth("runtime", ComponentStatus.HEALTHY))
    monitor.register_check("browser", lambda: ComponentHealth("browser", ComponentStatus.DEGRADED))
    assert monitor.run().overall_status == ComponentStatus.DEGRADED


def test_a_raising_check_is_reported_as_down_without_crashing_the_run():
    monitor = PlatformHealthMonitor()

    def broken_check():
        raise RuntimeError("boom")

    monitor.register_check("broken", broken_check)
    monitor.register_check("fine", lambda: ComponentHealth("fine", ComponentStatus.HEALTHY))

    report = monitor.run()

    broken_component = next(c for c in report.components if c.name == "broken")
    assert broken_component.status == ComponentStatus.DOWN
    assert "boom" in broken_component.detail
    assert report.overall_status == ComponentStatus.DOWN
