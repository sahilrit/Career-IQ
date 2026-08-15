"""Invoice: tracks a payment owed against a Contract."""

from __future__ import annotations

import uuid
from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "invoice"
_OUTSTANDING_STATUSES = frozenset({"sent", "overdue"})


class InvoiceStatus(StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"


class Invoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    contract_id: str
    amount: float
    issued_date: date
    due_date: date
    status: InvoiceStatus = InvoiceStatus.DRAFT


class InvoiceRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, invoice: Invoice) -> None:
        self._store.put(_ENTITY_TYPE, invoice.id, invoice.model_dump(mode="json"))

    def list_for_contract(self, contract_id: str) -> list[Invoice]:
        return [
            Invoice.model_validate(data)
            for data in self._store.list(_ENTITY_TYPE)
            if data.get("contract_id") == contract_id
        ]


def outstanding_balance(invoices: list[Invoice]) -> float:
    return sum(
        invoice.amount for invoice in invoices if invoice.status.value in _OUTSTANDING_STATUSES
    )
