"""CredentialVault: encrypted storage for user-supplied credentials, with
every access permission-checked and audited.

    Agent != credential owner. Agents request capabilities; the platform
    authorizes access.

A plugin/agent never receives raw ciphertext or an unchecked decrypt
call — every operation goes through ``check_access`` against the
requester's declared manifest permissions (Phase 3) first, and every
attempt, successful or not, is written to the audit log.
"""

from __future__ import annotations

from careeros_common import DocumentStore
from careeros_credentials.audit import AccessRecord, CredentialAuditLog
from careeros_credentials.encryption import SecretCipher
from careeros_credentials.exceptions import SecretNotFoundError
from careeros_credentials.permissions import PermissionLookup, check_access

_ENTITY_TYPE = "encrypted_secret"


class CredentialVault:
    def __init__(
        self,
        store: DocumentStore,
        cipher: SecretCipher,
        audit_log: CredentialAuditLog,
        *,
        lookup_permissions: PermissionLookup,
    ) -> None:
        self._store = store
        self._cipher = cipher
        self._audit = audit_log
        self._lookup_permissions = lookup_permissions

    def store_secret(
        self, identity_id: str, service: str, value: str, *, requester_id: str
    ) -> None:
        self._authorize_or_log(identity_id, service, "store", requester_id)
        encrypted = self._cipher.encrypt(value)
        self._store.put(_ENTITY_TYPE, self._key(identity_id, service), {"ciphertext": encrypted})
        self._audit.record(
            AccessRecord(
                identity_id=identity_id,
                service=service,
                action="store",
                requester_id=requester_id,
                success=True,
            )
        )

    def get_secret(self, identity_id: str, service: str, *, requester_id: str) -> str:
        self._authorize_or_log(identity_id, service, "retrieve", requester_id)

        data = self._store.get_or_none(_ENTITY_TYPE, self._key(identity_id, service))
        if data is None:
            self._audit.record(
                AccessRecord(
                    identity_id=identity_id,
                    service=service,
                    action="retrieve",
                    requester_id=requester_id,
                    success=False,
                    detail="not found",
                )
            )
            raise SecretNotFoundError(
                f"No {service!r} credential stored for identity {identity_id!r}"
            )

        value = self._cipher.decrypt(data["ciphertext"])
        self._audit.record(
            AccessRecord(
                identity_id=identity_id,
                service=service,
                action="retrieve",
                requester_id=requester_id,
                success=True,
            )
        )
        return value

    def rotate_secret(
        self, identity_id: str, service: str, new_value: str, *, requester_id: str
    ) -> None:
        self._authorize_or_log(identity_id, service, "rotate", requester_id)
        encrypted = self._cipher.encrypt(new_value)
        self._store.put(_ENTITY_TYPE, self._key(identity_id, service), {"ciphertext": encrypted})
        self._audit.record(
            AccessRecord(
                identity_id=identity_id,
                service=service,
                action="rotate",
                requester_id=requester_id,
                success=True,
            )
        )

    def delete_secret(self, identity_id: str, service: str, *, requester_id: str) -> None:
        self._authorize_or_log(identity_id, service, "delete", requester_id)
        self._store.delete(_ENTITY_TYPE, self._key(identity_id, service))
        self._audit.record(
            AccessRecord(
                identity_id=identity_id,
                service=service,
                action="delete",
                requester_id=requester_id,
                success=True,
            )
        )

    def has_secret(self, identity_id: str, service: str) -> bool:
        return self._store.get_or_none(_ENTITY_TYPE, self._key(identity_id, service)) is not None

    def _authorize_or_log(
        self, identity_id: str, service: str, action: str, requester_id: str
    ) -> None:
        try:
            check_access(requester_id, service, self._lookup_permissions)
        except Exception as exc:
            self._audit.record(
                AccessRecord(
                    identity_id=identity_id,
                    service=service,
                    action=action,
                    requester_id=requester_id,
                    success=False,
                    detail=str(exc),
                )
            )
            raise

    def _key(self, identity_id: str, service: str) -> str:
        return f"{identity_id}:{service}"
