"""Company: a prospective freelance client, tracked from first discovery
through to a won contract. Deliberately separate from
careeros_opportunity_intelligence.Client (Phase 20) — a Company is a
*prospect* being worked through the acquisition pipeline; it only
becomes a Client once the CONTRACT stage closes (see
``ClientAcquisitionDivision.mark_client_won``).
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "company"


class Company(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    website: str
    industry: str = ""
    contact_name: str | None = None
    contact_email: str | None = None
    notes: str = ""


class CompanyRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, company: Company) -> None:
        self._store.put(_ENTITY_TYPE, company.id, company.model_dump(mode="json"))

    def load(self, company_id: str) -> Company:
        return Company.model_validate(self._store.get(_ENTITY_TYPE, company_id))

    def load_or_none(self, company_id: str) -> Company | None:
        data = self._store.get_or_none(_ENTITY_TYPE, company_id)
        return Company.model_validate(data) if data is not None else None

    def list_all(self) -> list[Company]:
        return [Company.model_validate(data) for data in self._store.list(_ENTITY_TYPE)]
