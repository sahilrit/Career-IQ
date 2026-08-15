"""careeros_marketplace_governance: Marketplace Governance.

Manifest validation, version validation, permission review, dependency
validation, security scanning, capability declarations, a real
build-time compatibility smoke test, plugin version history, and
rollback — the checks a plugin must pass before distribution, so the
ecosystem doesn't become dangerous or unstable.
"""

from careeros_marketplace_governance.checks import (
    capability_declaration_check,
    compatibility_check,
    dependency_validation_check,
    manifest_authoring_check,
    permission_review_check,
    security_scan_check,
    version_check,
)
from careeros_marketplace_governance.exceptions import (
    MarketplaceGovernanceError,
    VersionNotFoundError,
)
from careeros_marketplace_governance.governance_review import (
    GovernanceReport,
    run_governance_review,
)
from careeros_marketplace_governance.marketplace_governance_division import (
    MarketplaceGovernanceDivision,
)
from careeros_marketplace_governance.review_check import CheckSeverity, ReviewCheckResult
from careeros_marketplace_governance.version_rollback import (
    PluginVersionRecord,
    PluginVersionRepository,
    current_version,
    publish_version,
    rollback_to,
)

__all__ = [
    "CheckSeverity",
    "GovernanceReport",
    "MarketplaceGovernanceDivision",
    "MarketplaceGovernanceError",
    "PluginVersionRecord",
    "PluginVersionRepository",
    "ReviewCheckResult",
    "VersionNotFoundError",
    "capability_declaration_check",
    "compatibility_check",
    "current_version",
    "dependency_validation_check",
    "manifest_authoring_check",
    "permission_review_check",
    "publish_version",
    "rollback_to",
    "run_governance_review",
    "security_scan_check",
    "version_check",
]
