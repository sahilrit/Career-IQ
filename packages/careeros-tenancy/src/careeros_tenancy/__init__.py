"""careeros_tenancy: SaaS identity and multi-tenancy. Workspace is the
isolation boundary; TenantScopedDocumentStore is the concrete mechanism
guaranteeing customer A can never access customer B's data, applied to
every already-shipped DocumentStore-backed repository with zero changes
to those packages.
"""

from careeros_tenancy.access_control import has_permission, require_permission
from careeros_tenancy.exceptions import PermissionDeniedError, TenancyError
from careeros_tenancy.models import (
    ROLE_PERMISSIONS,
    Membership,
    Organization,
    Permission,
    Role,
    User,
    Workspace,
)
from careeros_tenancy.repository import TenancyRepository
from careeros_tenancy.tenant_store import TenantScopedDocumentStore

__all__ = [
    "ROLE_PERMISSIONS",
    "Membership",
    "Organization",
    "Permission",
    "PermissionDeniedError",
    "Role",
    "TenancyError",
    "TenancyRepository",
    "TenantScopedDocumentStore",
    "User",
    "Workspace",
    "has_permission",
    "require_permission",
]
