"""Data retention: how long a given entity type may be kept before it's
overdue for deletion. Pure functions over caller-supplied timestamps —
this module doesn't reach into other packages' storage itself, so any
repository can be checked against a policy without a new dependency.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from careeros_common import DocumentStore

_ENTITY_TYPE = "compliance_retention_policy"


class RetentionPolicy(BaseModel):
    entity_type: str
    retention_days: int


def is_expired(created_at: datetime, policy: RetentionPolicy, *, now: datetime) -> bool:
    return (now - created_at).days >= policy.retention_days


def find_expired(
    records: dict[str, datetime], policy: RetentionPolicy, *, now: datetime
) -> list[str]:
    return [
        record_id
        for record_id, created_at in records.items()
        if is_expired(created_at, policy, now=now)
    ]


class RetentionPolicyRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, policy: RetentionPolicy) -> None:
        self._store.put(_ENTITY_TYPE, policy.entity_type, policy.model_dump(mode="json"))

    def load(self, entity_type: str) -> RetentionPolicy | None:
        data = self._store.get_or_none(_ENTITY_TYPE, entity_type)
        return RetentionPolicy.model_validate(data) if data else None

    def list_all(self) -> list[RetentionPolicy]:
        return [RetentionPolicy.model_validate(data) for data in self._store.list(_ENTITY_TYPE)]
