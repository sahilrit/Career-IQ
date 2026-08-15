"""Tests for launch readiness checks."""

from __future__ import annotations

from careeros_launch import DEFAULT_LAUNCH_PROPERTIES, verify_launch_readiness


def test_all_satisfied_and_no_violations_is_ready():
    report = verify_launch_readiness(
        [("multi_tenant", "careeros_tenancy")],
        zero_cost_violations={},
        import_checker=lambda _: True,
    )
    assert report.is_ready is True
    assert report.unsatisfied_properties == []


def test_unsatisfied_property_blocks_readiness():
    report = verify_launch_readiness(
        [("multi_tenant", "careeros_tenancy"), ("plugin_based", "careeros_plugin_sdk")],
        zero_cost_violations={},
        import_checker=lambda package: package != "careeros_plugin_sdk",
    )
    assert report.is_ready is False
    assert [p.property_name for p in report.unsatisfied_properties] == ["plugin_based"]


def test_zero_cost_violations_block_readiness_even_if_properties_pass():
    report = verify_launch_readiness(
        [("multi_tenant", "careeros_tenancy")],
        zero_cost_violations={"some-package": ["openai"]},
        import_checker=lambda _: True,
    )
    assert report.is_ready is False


def test_default_properties_are_all_real_installed_packages():
    report = verify_launch_readiness(DEFAULT_LAUNCH_PROPERTIES, zero_cost_violations={})
    assert report.unsatisfied_properties == []
