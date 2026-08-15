"""Tests for compute_platform_performance."""

from __future__ import annotations

from careeros_analytics import compute_platform_performance
from careeros_career_brain import Application


def test_groups_by_source_provider():
    applications = [
        Application(job_title="A", company_name="X", source_provider="remoteok"),
        Application(job_title="B", company_name="Y", source_provider="fiverr"),
        Application(job_title="C", company_name="Z", source_provider="remoteok"),
    ]
    performance = compute_platform_performance(applications)
    assert set(performance) == {"remoteok", "fiverr"}
    assert performance["remoteok"].discovered_count == 2
    assert performance["fiverr"].discovered_count == 1


def test_missing_provider_groups_under_unknown():
    applications = [Application(job_title="A", company_name="X")]
    performance = compute_platform_performance(applications)
    assert performance["unknown"].discovered_count == 1
