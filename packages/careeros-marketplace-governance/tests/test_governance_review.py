"""Tests for run_governance_review."""

from __future__ import annotations

from careeros_marketplace_governance import run_governance_review
from careeros_plugin_sdk import PluginManifest


def test_clean_manifest_with_successful_build_passes(manifest):
    report = run_governance_review(manifest, build_fn=lambda: object())
    assert report.passed is True
    assert report.errors == []


def test_placeholder_version_fails_the_review():
    manifest = PluginManifest(id="p", name="P", version="0.0.0", description="x", actions=["a"])
    report = run_governance_review(manifest, build_fn=lambda: object())
    assert report.passed is False
    assert any(error.check_name == "version" for error in report.errors)


def test_dangerous_permission_fails_the_review():
    manifest = PluginManifest(
        id="p",
        name="P",
        version="1.0.0",
        description="x",
        actions=["a"],
        permissions=["delete_all_data"],
    )
    report = run_governance_review(
        manifest,
        allowed_permissions=frozenset({"delete_all_data"}),
        dangerous_permissions=frozenset({"delete_all_data"}),
        build_fn=lambda: object(),
    )
    assert report.passed is False


def test_unknown_dependency_fails_the_review():
    manifest = PluginManifest(
        id="p",
        name="P",
        version="1.0.0",
        description="x",
        actions=["a"],
        dependencies={"careeros-missing": "^1.0.0"},
    )
    report = run_governance_review(manifest, build_fn=lambda: object())
    assert report.passed is False


def test_failing_build_fn_fails_the_review(manifest):
    def failing():
        raise RuntimeError("boom")

    report = run_governance_review(manifest, build_fn=failing)
    assert report.passed is False


def test_warning_only_issues_do_not_fail_the_review():
    manifest = PluginManifest(id="p", name="P", version="1.0.0", actions=["a"])
    report = run_governance_review(manifest, build_fn=lambda: object())
    assert report.passed is True
