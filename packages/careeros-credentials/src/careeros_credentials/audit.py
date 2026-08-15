"""CredentialAuditLog: every vault access, recorded — who touched which
secret, when, and whether it succeeded.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "credential_access"


class AccessRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    identity_id: str
    service: str
    action: str  # "store", "retrieve", "rotate", "delete"
    requester_id: str
    success: bool
    detail: str = ""
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CredentialAuditLog:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def record(self, record: AccessRecord) -> None:
        self._store.put(_ENTITY_TYPE, record.id, record.model_dump(mode="json"))

    def for_identity(self, identity_id: str) -> list[AccessRecord]:
        records = [
            AccessRecord.model_validate(data)
            for data in self._store.list(_ENTITY_TYPE)
            if data.get("identity_id") == identity_id
        ]
        return sorted(records, key=lambda record: record.occurred_at)

    def for_service(self, identity_id: str, service: str) -> list[AccessRecord]:
        return [record for record in self.for_identity(identity_id) if record.service == service]
