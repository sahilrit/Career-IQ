"""IncomeRecord: one real, received payment — salary, freelance
revenue, or client revenue. Nothing projected or invented lives here;
projections (annualized freelance income, trends) are computed
separately from these real records.
"""

from __future__ import annotations

import uuid
from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "income_record"


class IncomeSource(StrEnum):
    SALARY = "salary"
    FREELANCE = "freelance"
    CLIENT_REVENUE = "client_revenue"
    OTHER = "other"


class IncomeRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: IncomeSource
    source_name: str
    amount: float
    received_date: date
    hours_worked: float | None = Field(
        default=None, description="Hours worked to earn this amount, if known."
    )


class IncomeRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, record: IncomeRecord) -> None:
        self._store.put(_ENTITY_TYPE, record.id, record.model_dump(mode="json"))

    def load(self, record_id: str) -> IncomeRecord:
        return IncomeRecord.model_validate(self._store.get(_ENTITY_TYPE, record_id))

    def list_all(self) -> list[IncomeRecord]:
        return [IncomeRecord.model_validate(data) for data in self._store.list(_ENTITY_TYPE)]

    def list_by_source(self, source: IncomeSource) -> list[IncomeRecord]:
        return [record for record in self.list_all() if record.source == source]
