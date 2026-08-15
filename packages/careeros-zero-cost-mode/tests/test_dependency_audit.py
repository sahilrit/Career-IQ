"""Tests for scan_dependencies (pure) and read_workspace_dependencies
(real filesystem scan via tomllib).
"""

from __future__ import annotations

from pathlib import Path

from careeros_zero_cost_mode import read_workspace_dependencies, scan_dependencies


def test_clean_packages_are_omitted():
    result = scan_dependencies({"careeros-common": ["pydantic>=2.0", "httpx"]})
    assert result == {}


def test_flags_a_known_paid_package():
    result = scan_dependencies({"careeros-ai": ["openai>=1.0", "pydantic"]})
    assert result == {"careeros-ai": ["openai>=1.0"]}


def test_matches_regardless_of_version_specifier_style():
    result = scan_dependencies({"a": ["stripe==5.0"], "b": ["stripe"], "c": ["stripe[async]>=2"]})
    assert set(result) == {"a", "b", "c"}


def test_custom_known_paid_packages_override_the_default_list():
    custom = frozenset({"some-internal-paid-thing"})
    result = scan_dependencies({"a": ["some-internal-paid-thing"]}, known_paid_packages=custom)
    assert result == {"a": ["some-internal-paid-thing"]}


def test_read_workspace_dependencies_against_the_real_repo_finds_no_paid_sdks():
    packages_dir = Path(__file__).resolve().parents[2]
    dependencies_by_package = read_workspace_dependencies(packages_dir)
    assert len(dependencies_by_package) > 40
    assert scan_dependencies(dependencies_by_package) == {}
