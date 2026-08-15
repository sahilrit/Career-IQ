"""Role-based access control: does this role have this permission?"""

from __future__ import annotations

from careeros_tenancy.exceptions import PermissionDeniedError
from careeros_tenancy.models import ROLE_PERMISSIONS, Permission, Role


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS[role]


def require_permission(role: Role, permission: Permission) -> None:
    if not has_permission(role, permission):
        raise PermissionDeniedError(
            f"Role {role.value!r} does not have permission {permission.value!r}"
        )
