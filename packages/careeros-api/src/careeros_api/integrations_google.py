"""Google integration: OAuth connect + Gmail send + Calendar, over plain
HTTPS (no Google SDK, to keep the image slim). The workspace connects its
own Google account; we store only the long-lived refresh token, encrypted.

Inert until CAREEROS_GOOGLE_CLIENT_ID / _SECRET are set."""

from __future__ import annotations

import base64
import json
import os
from email.message import EmailMessage
from typing import Any
from urllib.parse import urlencode

import httpx

from careeros_api.email import app_base_url
from careeros_api.vault_support import open_vault

_SERVICE = "google_oauth"
_REQUESTER = "careeros-app"

_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
_GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
_CALENDAR_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

SCOPES = " ".join(
    [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
    ]
)


class GoogleError(Exception):
    """Google API / OAuth failure."""


class GoogleNotConnectedError(GoogleError):
    """The workspace hasn't connected a Google account."""


def client_id() -> str:
    return os.environ.get("CAREEROS_GOOGLE_CLIENT_ID", "")


def _client_secret() -> str:
    return os.environ.get("CAREEROS_GOOGLE_CLIENT_SECRET", "")


def configured() -> bool:
    return bool(client_id() and _client_secret())


def redirect_uri() -> str:
    return f"{app_base_url()}/settings/google/callback"


def build_auth_url(state: str) -> str:
    params = {
        "client_id": client_id(),
        "redirect_uri": redirect_uri(),
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    return f"{_AUTH_URL}?{urlencode(params)}"


def _post_token(data: dict[str, str]) -> dict[str, Any]:
    try:
        response = httpx.post(_TOKEN_URL, data=data, timeout=30.0)
    except httpx.HTTPError as error:
        raise GoogleError(str(error)) from error
    if response.status_code >= 400:
        raise GoogleError(f"token endpoint returned {response.status_code}: {response.text[:200]}")
    return response.json()


def exchange_code(code: str) -> dict[str, Any]:
    return _post_token(
        {
            "code": code,
            "client_id": client_id(),
            "client_secret": _client_secret(),
            "redirect_uri": redirect_uri(),
            "grant_type": "authorization_code",
        }
    )


def _access_token_from_refresh(refresh_token: str) -> str:
    tokens = _post_token(
        {
            "refresh_token": refresh_token,
            "client_id": client_id(),
            "client_secret": _client_secret(),
            "grant_type": "refresh_token",
        }
    )
    token = tokens.get("access_token")
    if not token:
        raise GoogleError("no access token returned on refresh")
    return token


def userinfo_email(access_token: str) -> str:
    try:
        response = httpx.get(
            _USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=30.0
        )
    except httpx.HTTPError:
        return ""
    if response.status_code >= 400:
        return ""
    return response.json().get("email", "")


# --- Persistence (encrypted vault) ------------------------------------------


def store_connection(store: Any, workspace_id: str, refresh_token: str, email: str) -> None:
    payload = json.dumps({"refresh_token": refresh_token, "email": email})
    open_vault(store, _SERVICE).store_secret(
        workspace_id, _SERVICE, payload, requester_id=_REQUESTER
    )


def connection(store: Any, workspace_id: str) -> dict[str, str] | None:
    vault = open_vault(store, _SERVICE)
    if not vault.has_secret(workspace_id, _SERVICE):
        return None
    raw = vault.get_secret(workspace_id, _SERVICE, requester_id=_REQUESTER)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def disconnect(store: Any, workspace_id: str) -> None:
    vault = open_vault(store, _SERVICE)
    if vault.has_secret(workspace_id, _SERVICE):
        vault.delete_secret(workspace_id, _SERVICE, requester_id=_REQUESTER)


def _access_token(store: Any, workspace_id: str) -> str:
    conn = connection(store, workspace_id)
    if conn is None:
        raise GoogleNotConnectedError("connect a Google account first")
    return _access_token_from_refresh(conn["refresh_token"])


# --- Gmail + Calendar --------------------------------------------------------


def send_gmail(store: Any, workspace_id: str, *, to: str, subject: str, body: str) -> None:
    access_token = _access_token(store, workspace_id)
    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    try:
        response = httpx.post(
            _GMAIL_SEND_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            json={"raw": raw},
            timeout=30.0,
        )
    except httpx.HTTPError as error:
        raise GoogleError(str(error)) from error
    if response.status_code >= 400:
        raise GoogleError(f"Gmail send failed ({response.status_code}): {response.text[:200]}")


def list_events(
    store: Any, workspace_id: str, *, time_min_iso: str, max_results: int = 10
) -> list[dict[str, Any]]:
    access_token = _access_token(store, workspace_id)
    params = {
        "timeMin": time_min_iso,
        "maxResults": str(max_results),
        "orderBy": "startTime",
        "singleEvents": "true",
    }
    try:
        response = httpx.get(
            _CALENDAR_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
            timeout=30.0,
        )
    except httpx.HTTPError as error:
        raise GoogleError(str(error)) from error
    if response.status_code >= 400:
        raise GoogleError(f"Calendar list failed ({response.status_code})")
    items = response.json().get("items", [])
    events = []
    for item in items:
        start = item.get("start", {})
        events.append(
            {
                "summary": item.get("summary", "(no title)"),
                "start": start.get("dateTime") or start.get("date") or "",
                "html_link": item.get("htmlLink", ""),
            }
        )
    return events


def create_event(
    store: Any,
    workspace_id: str,
    *,
    summary: str,
    start_iso: str,
    end_iso: str,
    attendees: list[str] | None = None,
) -> dict[str, Any]:
    access_token = _access_token(store, workspace_id)
    payload: dict[str, Any] = {
        "summary": summary,
        "start": {"dateTime": start_iso},
        "end": {"dateTime": end_iso},
    }
    if attendees:
        payload["attendees"] = [{"email": email} for email in attendees]
    try:
        response = httpx.post(
            _CALENDAR_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            params={"sendUpdates": "all"},  # email the invite to attendees
            json=payload,
            timeout=30.0,
        )
    except httpx.HTTPError as error:
        raise GoogleError(str(error)) from error
    if response.status_code >= 400:
        raise GoogleError(f"Calendar create failed ({response.status_code}): {response.text[:200]}")
    data = response.json()
    return {"id": data.get("id", ""), "html_link": data.get("htmlLink", "")}
