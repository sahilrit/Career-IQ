"""careeros_compliance: Security / Compliance / Data Portability.

Tenant isolation (Phase 25), encryption/OAuth/secrets (Phase 26), and
consent/audit/per-identity data export & deletion (Phase 45) already
exist — this package covers what those didn't: retention policies,
configurable security policies, whole-account deletion spanning both
domain data and tenancy records, and a compliance readiness report.
"""

from careeros_compliance.account_deletion import AccountDeletionCoordinator, AccountDeletionReceipt
from careeros_compliance.compliance_report import ComplianceReport, generate_compliance_report
from careeros_compliance.exceptions import ComplianceError
from careeros_compliance.retention import (
    RetentionPolicy,
    RetentionPolicyRepository,
    find_expired,
    is_expired,
)
from careeros_compliance.security_policy import SecurityPolicy, check_password

__all__ = [
    "AccountDeletionCoordinator",
    "AccountDeletionReceipt",
    "ComplianceError",
    "ComplianceReport",
    "RetentionPolicy",
    "RetentionPolicyRepository",
    "SecurityPolicy",
    "check_password",
    "find_expired",
    "generate_compliance_report",
    "is_expired",
]
