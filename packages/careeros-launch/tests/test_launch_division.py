"""Tests for the LaunchDivision facade."""

from __future__ import annotations

from pathlib import Path

import pytest

from careeros_launch import LaunchDivision, LaunchNotReadyError, LaunchReadinessReport
from careeros_launch import launch_division as launch_division_module

_PACKAGES_DIR = Path(__file__).resolve().parents[2]


def test_check_readiness_against_the_real_workspace_is_ready(store):
    division = LaunchDivision(store)
    report = division.check_readiness(packages_dir=_PACKAGES_DIR)
    assert report.is_ready is True


def test_announce_launch_records_a_launch_when_ready(store):
    division = LaunchDivision(store)
    record = division.announce_launch(
        version="1.0.0", notes="Public launch", packages_dir=_PACKAGES_DIR
    )
    assert record.version == "1.0.0"
    assert division.latest_launch() == record


def test_announce_launch_refuses_when_gate_fails(store, monkeypatch):
    division = LaunchDivision(store)
    monkeypatch.setattr(
        launch_division_module,
        "verify_launch_readiness",
        lambda *args, **kwargs: LaunchReadinessReport(
            properties=[], zero_cost_violations={"some-package": ["openai"]}
        ),
    )
    with pytest.raises(LaunchNotReadyError):
        division.announce_launch(version="1.0.0", packages_dir=_PACKAGES_DIR)


def test_latest_launch_of_no_launches_is_none(store):
    division = LaunchDivision(store)
    assert division.latest_launch() is None
