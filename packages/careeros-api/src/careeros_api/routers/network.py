"""Network (CRM) endpoints: list and add contacts."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from careeros_api.dependencies import Context
from careeros_api.schemas import ContactCreateRequest, ContactResponse
from careeros_crm import (
    Contact,
    ContactRepository,
    ContactRole,
    RelationshipCRM,
    TimelineRepository,
)

router = APIRouter(prefix="/contacts", tags=["network"])


def _crm(context: Context) -> RelationshipCRM:
    return RelationshipCRM(ContactRepository(context.store), TimelineRepository(context.store))


def _to_response(crm: RelationshipCRM, contact: Contact) -> ContactResponse:
    stage = crm.timeline_for(contact.id).current_stage
    return ContactResponse(
        id=contact.id,
        name=contact.name,
        role=contact.role.value,
        organization_name=contact.organization_name,
        stage=stage.value if stage else None,
        email=contact.email,
    )


@router.get("", response_model=list[ContactResponse])
def list_contacts(context: Context) -> list[ContactResponse]:
    crm = _crm(context)
    return [_to_response(crm, contact) for contact in crm.list_contacts()]


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
def add_contact(body: ContactCreateRequest, context: Context) -> ContactResponse:
    try:
        role = ContactRole(body.role)
    except ValueError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "unknown role") from error
    crm = _crm(context)
    contact = Contact(
        name=body.name, role=role, organization_name=body.organization_name, email=body.email
    )
    crm.add_contact(contact)
    return _to_response(crm, contact)
