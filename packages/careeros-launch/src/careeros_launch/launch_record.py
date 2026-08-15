"""LaunchRecord: a durable record of when production launch actually
happened — distinct from the readiness check itself, which can be run
any number of times before the real event is recorded.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "launch_record"


class LaunchRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    version: str
    notes: str = ""
    launched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LaunchRecordRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, record: LaunchRecord) -> None:
        self._store.put(_ENTITY_TYPE, record.id, record.model_dump(mode="json"))

    def list_all(self) -> list[LaunchRecord]:
        records = [LaunchRecord.model_validate(data) for data in self._store.list(_ENTITY_TYPE)]
        records.sort(key=lambda record: record.launched_at)
        return records

    def latest(self) -> LaunchRecord | None:
        records = self.list_all()
        return records[-1] if records else None
