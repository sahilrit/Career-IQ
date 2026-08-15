"""Contact: any person CareerOS has a relationship with, across both the
employment and freelance sides of the platform. Deliberately a separate,
lightweight identity from careeros_career_brain.Recruiter,
careeros_opportunity_intelligence.Client, and careeros_client_acquisition.Company
— those packages own the domain-specific record; a Contact just needs
enough to anchor a relationship timeline. Sharing the same ``id`` as the
underlying record (see ``careeros_crm.events``) is how the two line up
without duplicating data.
"""

from __future__ import annotations

import uuid
from enum import StrEnum

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

_ENTITY_TYPE = "contact"


class ContactRole(StrEnum):
    RECRUITER = "recruiter"
    FOUNDER = "founder"
    CMO = "cmo"
    HIRING_MANAGER = "hiring_manager"
    AGENCY_OWNER = "agency_owner"
    CLIENT = "client"
    PROSPECT = "prospect"


class Contact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: ContactRole
    organization_name: str = ""
    email: str | None = None
    notes: str = ""


class ContactRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, contact: Contact) -> None:
        self._store.put(_ENTITY_TYPE, contact.id, contact.model_dump(mode="json"))

    def load(self, contact_id: str) -> Contact:
        return Contact.model_validate(self._store.get(_ENTITY_TYPE, contact_id))

    def load_or_none(self, contact_id: str) -> Contact | None:
        data = self._store.get_or_none(_ENTITY_TYPE, contact_id)
        return Contact.model_validate(data) if data is not None else None

    def list_all(self) -> list[Contact]:
        return [Contact.model_validate(data) for data in self._store.list(_ENTITY_TYPE)]

    def list_by_role(self, role: ContactRole) -> list[Contact]:
        return [contact for contact in self.list_all() if contact.role == role]
