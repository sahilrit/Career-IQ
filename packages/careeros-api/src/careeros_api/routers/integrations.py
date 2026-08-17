"""Google integration endpoints: connect an account, send Gmail, and manage
Calendar events. All per-workspace; the refresh token is stored encrypted."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from careeros_api import integrations_google as google
from careeros_api.dependencies import Context

router = APIRouter(prefix="/integrations", tags=["integrations"])


class ConnectRequest(BaseModel):
    code: str = Field(min_length=1)


class SendEmailRequest(BaseModel):
    to: str = Field(min_length=3)
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)


class CreateEventRequest(BaseModel):
    summary: str = Field(min_length=1)
    start_iso: str = Field(min_length=1)
    end_iso: str = Field(min_length=1)
    attendees: list[str] = Field(default_factory=list)


def _require_configured() -> None:
    if not google.configured():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Google isn't configured on the server yet (missing client id/secret)",
        )


@router.get("/google")
def google_status(context: Context) -> dict[str, Any]:
    conn = google.connection(context.store, context.account.workspace_id)
    return {
        "configured": google.configured(),
        "connected": conn is not None,
        "email": conn["email"] if conn else None,
    }


@router.get("/google/auth-url")
def google_auth_url(context: Context) -> dict[str, str]:
    _require_configured()
    return {"url": google.build_auth_url(secrets.token_urlsafe(16))}


@router.post("/google/connect")
def google_connect(body: ConnectRequest, context: Context) -> dict[str, Any]:
    _require_configured()
    try:
        tokens = google.exchange_code(body.code)
    except google.GoogleError as error:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "couldn't complete Google sign-in"
        ) from error
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Google didn't return a refresh token — disconnect at "
            "myaccount.google.com/permissions and try connecting again",
        )
    email = google.userinfo_email(tokens.get("access_token", ""))
    google.store_connection(context.store, context.account.workspace_id, refresh_token, email)
    return {"connected": True, "email": email}


@router.delete("/google")
def google_disconnect(context: Context) -> dict[str, Any]:
    google.disconnect(context.store, context.account.workspace_id)
    return {"connected": False}


def _google_call(action):
    try:
        return action()
    except google.GoogleNotConnectedError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, "connect a Google account first") from error
    except google.GoogleError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(error)) from error


@router.post("/gmail/send")
def gmail_send(body: SendEmailRequest, context: Context) -> dict[str, bool]:
    _google_call(
        lambda: google.send_gmail(
            context.store,
            context.account.workspace_id,
            to=body.to,
            subject=body.subject,
            body=body.body,
        )
    )
    return {"sent": True}


@router.get("/calendar/events")
def calendar_events(context: Context) -> list[dict[str, Any]]:
    now = datetime.now(UTC).isoformat()
    return _google_call(
        lambda: google.list_events(context.store, context.account.workspace_id, time_min_iso=now)
    )


@router.post("/calendar/events", status_code=status.HTTP_201_CREATED)
def calendar_create(body: CreateEventRequest, context: Context) -> dict[str, Any]:
    return _google_call(
        lambda: google.create_event(
            context.store,
            context.account.workspace_id,
            summary=body.summary,
            start_iso=body.start_iso,
            end_iso=body.end_iso,
            attendees=body.attendees,
        )
    )
