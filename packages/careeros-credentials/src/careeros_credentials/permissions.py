"""PermissionChecker: enforces "agent != credential owner" — a plugin
must declare the matching permission in its manifest (Phase 3) before
the vault will hand it a decrypted secret.
"""

from __future__ import annotations

from collections.abc import Callable

from careeros_credentials.exceptions import AccessDeniedError

PermissionLookup = Callable[[str], frozenset[str]]  # plugin_id -> declared permissions


def credential_permission(service: str) -> str:
    return f"credential:{service}"


def check_access(plugin_id: str, service: str, lookup_permissions: PermissionLookup) -> None:
    required = credential_permission(service)
    declared = lookup_permissions(plugin_id)
    if required not in declared:
        raise AccessDeniedError(
            f"Plugin {plugin_id!r} has not declared permission {required!r}; access to "
            f"the {service!r} credential is denied."
        )
