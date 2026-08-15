"""Tests for the SelfHostedDivision facade."""

from __future__ import annotations

from careeros_self_hosted import SelfHostedDivision


def test_bootstrap_creates_the_data_dir(tmp_path):
    target = tmp_path / "data"
    division = SelfHostedDivision(target)
    result = division.bootstrap()
    assert result == target
    assert target.is_dir()


def test_platform_info_delegates(tmp_path):
    division = SelfHostedDivision(tmp_path)
    assert division.platform_info().python_version.startswith("3.")


def test_run_health_checks_delegates(tmp_path):
    division = SelfHostedDivision(tmp_path)
    assert len(division.run_health_checks()) == 4


def test_is_ready_delegates(tmp_path):
    division = SelfHostedDivision(tmp_path)
    assert division.is_ready() is True
