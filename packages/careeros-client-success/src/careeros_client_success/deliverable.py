"""Deliverable: a tracked unit of work within a Contract."""

from __future__ import annotations

import uuid
from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "deliverable"


class DeliverableStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    APPROVED = "approved"


class Deliverable(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    contract_id: str
    title: str
    description: str = ""
    due_date: date | None = None
    status: DeliverableStatus = DeliverableStatus.PENDING


class DeliverableRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, deliverable: Deliverable) -> None:
        self._store.put(_ENTITY_TYPE, deliverable.id, deliverable.model_dump(mode="json"))

    def load(self, deliverable_id: str) -> Deliverable:
        return Deliverable.model_validate(self._store.get(_ENTITY_TYPE, deliverable_id))

    def list_for_contract(self, contract_id: str) -> list[Deliverable]:
        return [
            Deliverable.model_validate(data)
            for data in self._store.list(_ENTITY_TYPE)
            if data.get("contract_id") == contract_id
        ]
