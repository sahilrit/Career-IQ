"""Application pipeline: list applications, advance one through its lifecycle,
and edit notes. The status state-machine lives in the domain
(Application.transition_to enforcing ALLOWED_STATUS_TRANSITIONS)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from careeros_api.dependencies import Context
from careeros_career_brain import (
    Application,
    ApplicationStatus,
    CareerBrainRepository,
    InvalidStatusTransitionError,
)
from careeros_tenancy import Permission

router = APIRouter(prefix="/applications", tags=["applications"])


class StatusTransitionRequest(BaseModel):
    to: str = Field(min_length=1, description="target status, e.g. 'applied'")
    note: str = ""


class NotesRequest(BaseModel):
    notes: str = ""


def _applications(context: Context) -> list[Application]:
    return [
        application
        for brain in CareerBrainRepository(context.store).list_all()
        for application in brain.applications
    ]


def _brain_with(context: Context, application_id: str):
    for brain in CareerBrainRepository(context.store).list_all():
        application = brain.find_application(application_id)
        if application is not None:
            return brain, application
    raise HTTPException(status.HTTP_404_NOT_FOUND, "application not found")


@router.get("")
def list_applications(context: Context) -> list[dict[str, Any]]:
    return [application.model_dump(mode="json") for application in _applications(context)]


@router.get("/board")
def board(context: Context) -> dict[str, Any]:
    """The pipeline grouped by status — powers the kanban board and the
    dashboard funnel tiles (Qualified / Applied / Interviewing / Offers)."""
    columns: dict[str, list[dict[str, Any]]] = {s.value: [] for s in ApplicationStatus}
    for application in _applications(context):
        columns[application.status.value].append(application.model_dump(mode="json"))
    return {
        "columns": columns,
        "counts": {name: len(items) for name, items in columns.items()},
        "total": sum(len(items) for items in columns.values()),
    }


@router.post("/{application_id}/status")
def advance_status(
    application_id: str, body: StatusTransitionRequest, context: Context
) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain, application = _brain_with(context, application_id)
    try:
        target = ApplicationStatus(body.to)
    except ValueError as error:
        valid = sorted(s.value for s in ApplicationStatus)
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, f"unknown status '{body.to}'; valid: {valid}"
        ) from error
    try:
        application.transition_to(target, note=body.note)
    except InvalidStatusTransitionError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    CareerBrainRepository(context.store).save(brain)
    return application.model_dump(mode="json")


@router.patch("/{application_id}")
def update_notes(application_id: str, body: NotesRequest, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain, application = _brain_with(context, application_id)
    application.notes = body.notes
    CareerBrainRepository(context.store).save(brain)
    return application.model_dump(mode="json")
