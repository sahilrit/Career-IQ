"""Network (CRM) endpoints: list and add contacts."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from careeros_ai import AIError
from careeros_api import ai_support
from careeros_api import integrations_google as google
from careeros_api.dependencies import Context
from careeros_api.outreach_support import AI_SYSTEM, KINDS, ai_prompt, draft_outreach
from careeros_api.schemas import ContactCreateRequest, ContactResponse
from careeros_career_brain import CareerBrainRepository
from careeros_crm import (
    Contact,
    ContactRepository,
    ContactRole,
    RelationshipCRM,
    RelationshipStage,
    TimelineRepository,
)

router = APIRouter(prefix="/contacts", tags=["network"])


class OutreachRequest(BaseModel):
    kind: str = Field(default="intro", description="intro | referral | thank_you")
    target_role: str = ""
    send: bool = False
    # When the user has edited the draft, send exactly what they approved.
    subject: str | None = None
    body: str | None = None


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


@router.post("/{contact_id}/outreach")
def outreach(contact_id: str, body: OutreachRequest, context: Context) -> dict[str, Any]:
    """Draft (and optionally send) a networking email grounded in the Career
    Brain. Sending goes through the user's connected Gmail and logs the
    interaction to the contact's timeline (advancing them to 'messaged')."""
    if body.kind not in KINDS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"kind must be one of {KINDS}")
    crm = _crm(context)
    contact = crm.get_contact(contact_id)
    if contact is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "contact not found")

    ai_used = False
    ai_error: str | None = None
    if body.subject is not None and body.body is not None:
        # The user approved/edited the draft — send exactly that.
        subject, draft = body.subject, body.body
    else:
        brains = CareerBrainRepository(context.store).list_all()
        brain = brains[0] if brains else None
        subject, draft = draft_outreach(
            kind=body.kind, contact=contact, brain=brain, target_role=body.target_role
        )
        client = ai_support.resolve_ai_client(context.store, context.account.workspace_id)
        if client is not None:
            prompt = ai_prompt(
                kind=body.kind, contact=contact, brain=brain, target_role=body.target_role
            )
            try:
                draft = client.complete(system=AI_SYSTEM, prompt=prompt).strip() or draft
                ai_used = True
            except AIError as error:
                ai_error = str(error)

    sent = False
    logged = False
    reason: str | None = None
    if body.send:
        if not contact.email:
            reason = "this contact has no email address"
        else:
            try:
                google.send_gmail(
                    context.store,
                    context.account.workspace_id,
                    to=contact.email,
                    subject=subject,
                    body=draft,
                )
                sent = True
                crm.record_engagement(
                    contact_id, RelationshipStage.MESSAGED, f"Sent {body.kind} email"
                )
                logged = True
            except google.GoogleNotConnectedError:
                reason = "connect Google in Settings first"
            except google.GoogleError as error:
                reason = str(error)

    return {
        "subject": subject,
        "body": draft,
        "sent": sent,
        "logged": logged,
        "reason": reason,
        "ai_used": ai_used,
        "ai_error": ai_error,
    }
