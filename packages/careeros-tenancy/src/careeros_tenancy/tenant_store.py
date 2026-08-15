"""TenantScopedDocumentStore: wraps a DocumentStore so every operation is
automatically namespaced to one tenant — the concrete mechanism behind
"customer A must never access customer B's data".

Every repository already built on DocumentStore (CareerBrainRepository,
HistoryLog, ClientRepository, DecisionMemory, ...) works completely
unmodified against this wrapper: it implements the same
put/get/get_or_none/delete/list interface, just with ``entity_type``
transparently prefixed by tenant. Hand a repository a
``TenantScopedDocumentStore`` instead of a raw ``DocumentStore`` and it
becomes tenant-isolated for free — no changes to any already-shipped
package required.
"""

from __future__ import annotations

from typing import Any

from careeros_common import DocumentStore


class TenantScopedDocumentStore:
    def __init__(self, store: DocumentStore, tenant_id: str) -> None:
        self._store = store
        self._tenant_id = tenant_id

    @property
    def tenant_id(self) -> str:
        return self._tenant_id

    def _scoped_type(self, entity_type: str) -> str:
        return f"tenant:{self._tenant_id}:{entity_type}"

    def put(self, entity_type: str, entity_id: str, data: dict[str, Any]) -> None:
        self._store.put(self._scoped_type(entity_type), entity_id, data)

    def get(self, entity_type: str, entity_id: str) -> dict[str, Any]:
        return self._store.get(self._scoped_type(entity_type), entity_id)

    def get_or_none(self, entity_type: str, entity_id: str) -> dict[str, Any] | None:
        return self._store.get_or_none(self._scoped_type(entity_type), entity_id)

    def delete(self, entity_type: str, entity_id: str) -> None:
        self._store.delete(self._scoped_type(entity_type), entity_id)

    def list(self, entity_type: str) -> list[dict[str, Any]]:
        return self._store.list(self._scoped_type(entity_type))
