"""General-purpose security audit log: every security-relevant action
(who did what to which resource, and when) — distinct from Phase 26's
CredentialAuditLog (credential access specifically) and Phase 5's
HistoryLog (business event history driven off the event bus). This one
exists for compliance/trust: "show me everything that happened to this
tenant's data."
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "audit_entry"


class AuditEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    tenant_id: str | None = None
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict = Field(default_factory=dict)


class AuditLogRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, entry: AuditEntry) -> None:
        self._store.put(_ENTITY_TYPE, entry.id, entry.model_dump(mode="json"))

    def list_all(self) -> list[AuditEntry]:
        entries = [AuditEntry.model_validate(data) for data in self._store.list(_ENTITY_TYPE)]
        entries.sort(key=lambda entry: entry.occurred_at)
        return entries

    def list_for_resource(self, resource_type: str, resource_id: str) -> list[AuditEntry]:
        return [
            entry
            for entry in self.list_all()
            if entry.resource_type == resource_type and entry.resource_id == resource_id
        ]

    def list_for_actor(self, actor_id: str) -> list[AuditEntry]:
        return [entry for entry in self.list_all() if entry.actor_id == actor_id]


def record_audit_event(
    repository: AuditLogRepository,
    *,
    actor_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    tenant_id: str | None = None,
    metadata: dict | None = None,
) -> AuditEntry:
    entry = AuditEntry(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        tenant_id=tenant_id,
        metadata=metadata or {},
    )
    repository.save(entry)
    return entry
