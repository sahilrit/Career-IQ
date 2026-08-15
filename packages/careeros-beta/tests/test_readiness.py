"""Tests for beta readiness checks."""

from __future__ import annotations

from careeros_beta import DEFAULT_BETA_COMPONENTS, verify_beta_readiness


def test_all_importable_is_ready():
    report = verify_beta_readiness(
        [("Career Brain", "careeros_career_brain"), ("Dashboard", "careeros_dashboard")],
        import_checker=lambda _: True,
    )
    assert report.is_ready is True
    assert report.missing == []


def test_any_missing_component_is_not_ready():
    report = verify_beta_readiness(
        [("Career Brain", "careeros_career_brain"), ("Dashboard", "careeros_dashboard")],
        import_checker=lambda package: package != "careeros_dashboard",
    )
    assert report.is_ready is False
    assert [status.component_name for status in report.missing] == ["Dashboard"]


def test_default_components_are_all_real_installed_packages():
    report = verify_beta_readiness(DEFAULT_BETA_COMPONENTS)
    assert report.is_ready is True
    assert len(report.statuses) == len(DEFAULT_BETA_COMPONENTS)


def test_unknown_package_is_reported_not_importable():
    report = verify_beta_readiness([("Ghost", "careeros_does_not_exist")])
    assert report.statuses[0].is_importable is False
    assert report.is_ready is False
