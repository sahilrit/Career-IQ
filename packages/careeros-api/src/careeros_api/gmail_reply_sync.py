"""Gmail-backed mailbox for reply tracking.

Adapts the workspace's connected Gmail account to the ``Mailbox`` protocol
``careeros_reply_tracking`` expects, so the tracking loop itself stays
free of any Google specifics and testable without a network.

Reads only — it uses the ``gmail.readonly`` scope and never modifies the
mailbox. Recruiter mail is what we care about, so the Gmail query narrows
to messages in the primary category within the lookback window before we
spend a round-trip fetching each body.
"""

from __future__ import annotations

import base64
from typing import Any

import httpx

from careeros_api.integrations_google import GoogleError, _access_token
from careeros_reply_tracking import EmailMessage

_GMAIL_LIST_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
_GMAIL_GET_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/{id}"


def _header(payload: dict[str, Any], name: str) -> str:
    for header in payload.get("headers", []):
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def _decode_part(data: str) -> str:
    try:
        return base64.urlsafe_b64decode(data.encode()).decode("utf-8", errors="replace")
    except (ValueError, UnicodeDecodeError):
        return ""


def _extract_body(payload: dict[str, Any]) -> str:
    """Walk the MIME tree for the first text part.

    Plain text is preferred; HTML is a fallback with its tags stripped
    crudely, since the classifier only needs the words.
    """
    mime = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")

    if mime == "text/plain" and body_data:
        return _decode_part(body_data)

    for part in payload.get("parts", []):
        text = _extract_body(part)
        if text:
            return text

    if mime == "text/html" and body_data:
        html = _decode_part(body_data)
        return _strip_tags(html)

    return ""


def _strip_tags(html: str) -> str:
    out: list[str] = []
    depth = 0
    for char in html:
        if char == "<":
            depth += 1
        elif char == ">":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(char)
    return " ".join("".join(out).split())


class GmailMailbox:
    """The connected Gmail account, as a reply-tracking ``Mailbox``."""

    def __init__(self, store: Any, workspace_id: str, *, timeout: float = 30.0) -> None:
        self._store = store
        self._workspace_id = workspace_id
        self._timeout = timeout

    def _get(self, url: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        access_token = _access_token(self._store, self._workspace_id)
        try:
            response = httpx.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
                params=params,
                timeout=self._timeout,
            )
        except httpx.HTTPError as error:
            raise GoogleError(str(error)) from error
        if response.status_code >= 400:
            raise GoogleError(f"Gmail read failed ({response.status_code}): {response.text[:200]}")
        return response.json()

    def recent_messages(self, *, days: int, max_messages: int) -> list[EmailMessage]:
        listing = self._get(
            _GMAIL_LIST_URL,
            params={
                "q": f"newer_than:{days}d category:primary",
                "maxResults": str(max_messages),
            },
        )
        messages: list[EmailMessage] = []
        for stub in listing.get("messages", []):
            message_id = stub.get("id")
            if not message_id:
                continue
            full = self._get(_GMAIL_GET_URL.format(id=message_id), params={"format": "full"})
            payload = full.get("payload", {})
            messages.append(
                EmailMessage(
                    id=message_id,
                    sender=_header(payload, "From"),
                    subject=_header(payload, "Subject"),
                    body=_extract_body(payload) or full.get("snippet", ""),
                )
            )
        return messages
