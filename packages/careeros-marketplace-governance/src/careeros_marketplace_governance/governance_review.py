"""GovernanceReport: combines every check into one pass/fail verdict.
Only an unresolved ERROR-severity check fails the review — WARNING and
INFO checks are visible but don't block distribution on their own.
"""

from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel

from careeros_marketplace_governance.checks import (
    capability_declaration_check,
    compatibility_check,
    dependency_validation_check,
    manifest_authoring_check,
    permission_review_check,
    security_scan_check,
    version_check,
)
from careeros_marketplace_governance.review_check import CheckSeverity, ReviewCheckResult
from careeros_plugin_sdk import PluginManifest


class GovernanceReport(BaseModel):
    plugin_id: str
    checks: list[ReviewCheckResult]

    @property
    def passed(self) -> bool:
        return not self.errors

    @property
    def errors(self) -> list[ReviewCheckResult]:
        return [c for c in self.checks if c.severity == CheckSeverity.ERROR and not c.passed]


def run_governance_review(
    manifest: PluginManifest,
    *,
    allowed_permissions: frozenset[str] = frozenset(),
    dangerous_permissions: frozenset[str] = frozenset(),
    known_plugin_ids: frozenset[str] = frozenset(),
    build_fn: Callable[[], object] | None = None,
) -> GovernanceReport:
    checks: list[ReviewCheckResult] = []
    checks.extend(manifest_authoring_check(manifest))
    checks.append(version_check(manifest))
    checks.extend(permission_review_check(manifest, allowed_permissions))
    checks.extend(security_scan_check(manifest, dangerous_permissions))
    checks.extend(dependency_validation_check(manifest, known_plugin_ids))
    checks.append(capability_declaration_check(manifest))
    checks.append(compatibility_check(build_fn))
    return GovernanceReport(plugin_id=manifest.id, checks=checks)
