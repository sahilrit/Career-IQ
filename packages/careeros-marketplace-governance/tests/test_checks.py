"""Tests for the individual governance checks."""

from __future__ import annotations

import pytest

from careeros_marketplace_governance import (
    CheckSeverity,
    capability_declaration_check,
    compatibility_check,
    dependency_validation_check,
    manifest_authoring_check,
    permission_review_check,
    security_scan_check,
    version_check,
)
from careeros_plugin_sdk import PluginManifest


def test_manifest_authoring_check_passes_for_a_clean_manifest(manifest):
    results = manifest_authoring_check(manifest)
    assert all(result.passed for result in results)


def test_manifest_authoring_check_flags_an_empty_description():
    manifest = PluginManifest(id="p", name="P", version="1.0.0", actions=["a"])
    results = manifest_authoring_check(manifest)
    assert any(not result.passed for result in results)


def test_version_check_flags_the_placeholder_version():
    manifest = PluginManifest(id="p", name="P", version="0.0.0")
    result = version_check(manifest)
    assert result.passed is False
    assert result.severity == CheckSeverity.ERROR


def test_version_check_passes_a_real_version(manifest):
    assert version_check(manifest).passed is True


def test_permission_review_passes_allowed_permissions():
    manifest = PluginManifest(id="p", name="P", version="1.0.0", permissions=["network"])
    results = permission_review_check(manifest, frozenset({"network"}))
    assert all(result.passed for result in results)


def test_permission_review_flags_unlisted_permissions():
    manifest = PluginManifest(id="p", name="P", version="1.0.0", permissions=["network"])
    results = permission_review_check(manifest, frozenset())
    assert any(not result.passed and result.severity == CheckSeverity.ERROR for result in results)


def test_security_scan_flags_dangerous_permissions():
    manifest = PluginManifest(id="p", name="P", version="1.0.0", permissions=["delete_all_data"])
    results = security_scan_check(manifest, frozenset({"delete_all_data"}))
    assert any(not result.passed for result in results)


def test_security_scan_passes_when_nothing_dangerous():
    manifest = PluginManifest(id="p", name="P", version="1.0.0", permissions=["network"])
    results = security_scan_check(manifest, frozenset({"delete_all_data"}))
    assert all(result.passed for result in results)


def test_dependency_validation_passes_known_dependencies():
    manifest = PluginManifest(
        id="p", name="P", version="1.0.0", dependencies={"careeros-core-plugin": "^1.0.0"}
    )
    results = dependency_validation_check(manifest, frozenset({"careeros-core-plugin"}))
    assert all(result.passed for result in results)


def test_dependency_validation_flags_unknown_dependencies():
    manifest = PluginManifest(
        id="p", name="P", version="1.0.0", dependencies={"careeros-missing": "^1.0.0"}
    )
    results = dependency_validation_check(manifest, frozenset())
    assert any(not result.passed for result in results)


def test_capability_declaration_flags_duplicates():
    manifest = PluginManifest(
        id="p", name="P", version="1.0.0", capabilities=["FIND_JOBS", "FIND_JOBS"]
    )
    result = capability_declaration_check(manifest)
    assert result.passed is False


def test_compatibility_check_passes_when_build_succeeds():
    result = compatibility_check(lambda: object())
    assert result.passed is True


def test_compatibility_check_fails_when_build_raises():
    def failing():
        raise RuntimeError("boom")

    result = compatibility_check(failing)
    assert result.passed is False
    assert result.severity == CheckSeverity.ERROR


def test_compatibility_check_warns_when_no_build_fn_given():
    result = compatibility_check(None)
    assert result.passed is False
    assert result.severity == CheckSeverity.WARNING


@pytest.mark.parametrize("permissions", [[], ["network"]])
def test_permission_review_handles_empty_and_nonempty(permissions):
    manifest = PluginManifest(id="p", name="P", version="1.0.0", permissions=permissions)
    results = permission_review_check(manifest, frozenset({"network"}))
    assert len(results) >= 1
