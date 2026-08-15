"""Contract: a scoped engagement with a client. ``client_id`` shares the
same id as the underlying careeros_opportunity_intelligence.Client
record, the same lining-up-without-duplicating pattern Phase 33
established for Contact.
"""

from __future__ import annotations

import uuid
from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "contract"


class ContractStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    TERMINATED = "terminated"


class Contract(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    title: str
    scope: str = ""
    rate: float = 0.0
    start_date: date
    end_date: date | None = None
    status: ContractStatus = ContractStatus.DRAFT


class ContractRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, contract: Contract) -> None:
        self._store.put(_ENTITY_TYPE, contract.id, contract.model_dump(mode="json"))

    def load(self, contract_id: str) -> Contract:
        return Contract.model_validate(self._store.get(_ENTITY_TYPE, contract_id))

    def load_or_none(self, contract_id: str) -> Contract | None:
        data = self._store.get_or_none(_ENTITY_TYPE, contract_id)
        return Contract.model_validate(data) if data is not None else None

    def list_all(self) -> list[Contract]:
        return [Contract.model_validate(data) for data in self._store.list(_ENTITY_TYPE)]

    def list_for_client(self, client_id: str) -> list[Contract]:
        return [contract for contract in self.list_all() if contract.client_id == client_id]
