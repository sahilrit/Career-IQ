"""Application pipeline: list applications, advance one through its lifecycle,
and edit notes. The status state-machine lives in the domain
(Application.transition_to enforcing ALLOWED_STATUS_TRANSITIONS)."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from careeros_api import integrations_google as google
from careeros_api.dependencies import Context
from careeros_career_brain import (
    Application,
    ApplicationStatus,
    CareerBrainRepository,
    InvalidStatusTransitionError,
)
from careeros_job_discovery import JobPostingRepository, skill_gap
from careeros_tenancy import Permission

router = APIRouter(prefix="/applications", tags=["applications"])


class StatusTransitionRequest(BaseModel):
    to: str = Field(min_length=1, description="target status, e.g. 'applied'")
    note: str = ""


class NotesRequest(BaseModel):
    notes: str = ""


class FollowUpRequest(BaseModel):
    date: str | None = Field(default=None, description="ISO date; null clears the reminder")
    add_to_calendar: bool = False


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


@router.get("/follow-ups")
def follow_ups(context: Context) -> list[dict[str, Any]]:
    """Applications with a follow-up set, soonest first, each flagged as due
    when the date has arrived — powers the 'due soon' nudge."""
    today = date.today()
    items = []
    for application in _applications(context):
        if application.follow_up_date is None:
            continue
        payload = application.model_dump(mode="json")
        payload["days_until"] = (application.follow_up_date - today).days
        payload["due"] = application.follow_up_date <= today
        items.append(payload)
    items.sort(key=lambda item: item["follow_up_date"])
    return items


@router.patch("/{application_id}/follow-up")
def set_follow_up(application_id: str, body: FollowUpRequest, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    brain, application = _brain_with(context, application_id)
    if body.date is None:
        application.follow_up_date = None
    else:
        try:
            application.follow_up_date = date.fromisoformat(body.date)
        except ValueError as error:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "date must be ISO (YYYY-MM-DD)"
            ) from error
    CareerBrainRepository(context.store).save(brain)

    calendar: dict[str, Any] = {"created": False}
    if body.add_to_calendar and application.follow_up_date is not None:
        iso = application.follow_up_date.isoformat()
        try:
            event = google.create_event(
                context.store,
                context.account.workspace_id,
                summary=f"Follow up: {application.job_title} at {application.company_name}",
                start_iso=f"{iso}T09:00:00",
                end_iso=f"{iso}T09:30:00",
            )
            calendar = {"created": True, "html_link": event.get("htmlLink")}
        except google.GoogleNotConnectedError:
            calendar = {"created": False, "reason": "connect Google in Settings first"}
        except google.GoogleError as error:
            calendar = {"created": False, "reason": str(error)}

    return {"application": application.model_dump(mode="json"), "calendar": calendar}


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


@router.get("/{application_id}/gap")
def keyword_gap(application_id: str, context: Context) -> dict[str, Any]:
    """Why this scored the way it did: which of your skills the posting mentions,
    and which posting keywords are missing from your Career Brain."""
    brain, application = _brain_with(context, application_id)
    posting = (
        JobPostingRepository(context.store).load_or_none(application.job_url)
        if application.job_url
        else None
    )
    if posting is None:
        return {"available": False, "matched_skills": [], "missing_keywords": []}
    gap = skill_gap(posting, brain)
    return {"available": True, **gap}


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
