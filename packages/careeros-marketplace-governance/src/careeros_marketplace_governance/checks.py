"""The individual governance checks a plugin must pass before
distribution. Each is independently callable and testable — the review
report (see ``governance_review.py``) is just their combination.
"""

from __future__ import annotations

from collections.abc import Callable

from careeros_developer_sdk import validate_plugin_manifest
from careeros_marketplace_governance.review_check import CheckSeverity, ReviewCheckResult
from careeros_plugin_sdk import PluginManifest

_PLACEHOLDER_VERSION = "0.0.0"


def manifest_authoring_check(manifest: PluginManifest) -> list[ReviewCheckResult]:
    issues = validate_plugin_manifest(manifest)
    if not issues:
        return [
            ReviewCheckResult(
                check_name="manifest_authoring", severity=CheckSeverity.INFO, passed=True
            )
        ]
    return [
        ReviewCheckResult(
            check_name="manifest_authoring",
            severity=CheckSeverity.WARNING,
            passed=False,
            detail=issue,
        )
        for issue in issues
    ]


def version_check(manifest: PluginManifest) -> ReviewCheckResult:
    if manifest.version == _PLACEHOLDER_VERSION:
        return ReviewCheckResult(
            check_name="version",
            severity=CheckSeverity.ERROR,
            passed=False,
            detail="version 0.0.0 marks a placeholder — not ready for distribution",
        )
    return ReviewCheckResult(check_name="version", severity=CheckSeverity.INFO, passed=True)


def permission_review_check(
    manifest: PluginManifest, allowed_permissions: frozenset[str]
) -> list[ReviewCheckResult]:
    if not manifest.permissions:
        return [
            ReviewCheckResult(
                check_name="permission_review",
                severity=CheckSeverity.INFO,
                passed=True,
                detail="no permissions requested",
            )
        ]
    results = []
    for permission in manifest.permissions:
        if permission in allowed_permissions:
            results.append(
                ReviewCheckResult(
                    check_name=f"permission:{permission}", severity=CheckSeverity.INFO, passed=True
                )
            )
        else:
            results.append(
                ReviewCheckResult(
                    check_name=f"permission:{permission}",
                    severity=CheckSeverity.ERROR,
                    passed=False,
                    detail=f"{permission!r} is not on the reviewed allow-list",
                )
            )
    return results


def security_scan_check(
    manifest: PluginManifest, dangerous_permissions: frozenset[str]
) -> list[ReviewCheckResult]:
    hits = [
        permission for permission in manifest.permissions if permission in dangerous_permissions
    ]
    if not hits:
        return [
            ReviewCheckResult(check_name="security_scan", severity=CheckSeverity.INFO, passed=True)
        ]
    return [
        ReviewCheckResult(
            check_name="security_scan",
            severity=CheckSeverity.ERROR,
            passed=False,
            detail=f"requests dangerous permission {permission!r} — requires manual review",
        )
        for permission in hits
    ]


def dependency_validation_check(
    manifest: PluginManifest, known_plugin_ids: frozenset[str]
) -> list[ReviewCheckResult]:
    if not manifest.dependencies:
        return [
            ReviewCheckResult(
                check_name="dependency_validation",
                severity=CheckSeverity.INFO,
                passed=True,
                detail="no dependencies",
            )
        ]
    results = []
    for dependency_id, constraint in manifest.dependencies.items():
        if dependency_id in known_plugin_ids:
            results.append(
                ReviewCheckResult(
                    check_name=f"dependency:{dependency_id}",
                    severity=CheckSeverity.INFO,
                    passed=True,
                )
            )
        else:
            results.append(
                ReviewCheckResult(
                    check_name=f"dependency:{dependency_id}",
                    severity=CheckSeverity.ERROR,
                    passed=False,
                    detail=f"depends on {dependency_id!r}{constraint}, which is not a known plugin",
                )
            )
    return results


def capability_declaration_check(manifest: PluginManifest) -> ReviewCheckResult:
    if len(manifest.capabilities) != len(set(manifest.capabilities)):
        return ReviewCheckResult(
            check_name="capability_declaration",
            severity=CheckSeverity.WARNING,
            passed=False,
            detail="duplicate capability declared",
        )
    return ReviewCheckResult(
        check_name="capability_declaration", severity=CheckSeverity.INFO, passed=True
    )


def compatibility_check(build_fn: Callable[[], object] | None) -> ReviewCheckResult:
    if build_fn is None:
        return ReviewCheckResult(
            check_name="compatibility",
            severity=CheckSeverity.WARNING,
            passed=False,
            detail="no build function supplied to smoke-test",
        )
    try:
        build_fn()
    except Exception as error:
        return ReviewCheckResult(
            check_name="compatibility",
            severity=CheckSeverity.ERROR,
            passed=False,
            detail=str(error),
        )
    return ReviewCheckResult(check_name="compatibility", severity=CheckSeverity.INFO, passed=True)
