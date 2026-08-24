"""Tests for the Gmail reply-sync route and its MIME parsing.

The route is the seam between Gmail and the transport-agnostic tracking
loop, so these cover the adaptation (auth required, brain required, Gmail
payloads decoded) rather than the classification, which is tested in the
reply-tracking package.
"""

from __future__ import annotations

import base64

import pytest

from careeros_api import dependencies
from careeros_api.gmail_reply_sync import GmailMailbox, _extract_body, _header
from careeros_api.routers import integrations
from careeros_career_brain import Application, CareerBrain, CareerBrainRepository, Identity
from careeros_reply_tracking import EmailMessage
from careeros_tenancy import TenantScopedDocumentStore


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode()


def test_header_lookup_is_case_insensitive():
    payload = {"headers": [{"name": "From", "value": "recruiter@acme.com"}]}
    assert _header(payload, "from") == "recruiter@acme.com"


def test_extract_body_prefers_plain_text():
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [
            {"mimeType": "text/plain", "body": {"data": _b64("plain body")}},
            {"mimeType": "text/html", "body": {"data": _b64("<p>html body</p>")}},
        ],
    }
    assert _extract_body(payload) == "plain body"


def test_extract_body_falls_back_to_stripped_html():
    payload = {"mimeType": "text/html", "body": {"data": _b64("<p>Hello <b>there</b></p>")}}
    assert _extract_body(payload) == "Hello there"


def test_extract_body_handles_a_bare_text_payload():
    payload = {"mimeType": "text/plain", "body": {"data": _b64("just text")}}
    assert _extract_body(payload) == "just text"


class _FakeGmailMailbox:
    def recent_messages(self, *, days, max_messages):
        return [
            EmailMessage(
                id="m1",
                sender="recruiting@acme.com",
                subject="Acme interview",
                body="We'd like to invite you to an interview.",
            )
        ]


def test_sync_replies_requires_auth(client):
    assert client.post("/integrations/gmail/sync-replies").status_code == 401


def test_sync_replies_requires_a_career_brain(client, auth_headers):
    headers = auth_headers()
    assert client.post("/integrations/gmail/sync-replies", headers=headers).status_code == 404


def _seed_applied(headers, client) -> None:
    from careeros_career_brain import ApplicationStatus

    workspace_id = client.get("/auth/me", headers=headers).json()["workspace_id"]
    scoped = TenantScopedDocumentStore(dependencies.get_store(), workspace_id)
    repo = CareerBrainRepository(scoped)
    brain = CareerBrain(identity=Identity(full_name="Sahil", email="s@example.com"))
    brain.applications.append(
        Application(
            job_title="Performance Marketing Manager",
            company_name="Acme",
            status=ApplicationStatus.APPLIED,
        )
    )
    repo.save(brain)


def test_sync_replies_advances_an_application(client, auth_headers, monkeypatch):
    headers = auth_headers()
    _seed_applied(headers, client)

    # Swap the real Gmail mailbox for a fixture, so no network and no OAuth.
    monkeypatch.setattr(integrations, "GmailMailbox", lambda *args, **kwargs: _FakeGmailMailbox())

    response = client.post("/integrations/gmail/sync-replies", headers=headers)

    assert response.status_code == 200
    assert response.json()["transitioned"] == 1

    board = client.get("/applications", headers=headers).json()
    assert board[0]["status"] == "interviewing"


def test_gmail_mailbox_decodes_a_listing(monkeypatch):
    """The mailbox lists ids, then fetches each message and adapts it."""
    calls: list[str] = []

    def fake_get(self, url, params=None):
        calls.append(url)
        if url.endswith("/messages"):
            return {"messages": [{"id": "m1"}]}
        return {
            "snippet": "fallback",
            "payload": {
                "headers": [
                    {"name": "From", "value": "recruiting@acme.com"},
                    {"name": "Subject", "value": "Interview"},
                ],
                "mimeType": "text/plain",
                "body": {"data": _b64("We'd like to interview you.")},
            },
        }

    monkeypatch.setattr(GmailMailbox, "_get", fake_get)
    mailbox = GmailMailbox(store=None, workspace_id="w1")
    messages = mailbox.recent_messages(days=90, max_messages=10)

    assert len(messages) == 1
    assert messages[0].sender == "recruiting@acme.com"
    assert "interview" in messages[0].body.lower()


@pytest.mark.parametrize("scope", ["gmail.readonly", "gmail.send", "calendar.events"])
def test_the_readonly_scope_is_requested(scope):
    from careeros_api.integrations_google import SCOPES

    assert scope in SCOPES


# --- concurrent, fault-isolated message fetch (regression: serial N+1) --------


def test_messages_are_fetched_and_one_failure_does_not_sink_the_batch(monkeypatch):
    """Up to 100 messages were fetched serially in one request; one failing GET
    also aborted the whole scan. Fetch is now concurrent and per-message
    failures are isolated."""

    def fake_get(self, url, params=None):
        if url.endswith("/messages"):
            return {"messages": [{"id": "ok1"}, {"id": "boom"}, {"id": "ok2"}]}
        if "boom" in url:
            raise RuntimeError("500 on that message")
        mid = url.rstrip("/").split("/")[-1]
        return {
            "snippet": "s",
            "payload": {
                "headers": [
                    {"name": "From", "value": f"recruiting@{mid}.com"},
                    {"name": "Subject", "value": "hi"},
                ],
                "mimeType": "text/plain",
                "body": {"data": _b64("body")},
            },
        }

    monkeypatch.setattr(GmailMailbox, "_get", fake_get)
    messages = GmailMailbox(store=None, workspace_id="w1").recent_messages(days=90, max_messages=10)

    # The two good messages come back; the failing one is skipped, not fatal.
    assert {m.id for m in messages} == {"ok1", "ok2"}


def test_an_empty_listing_yields_no_messages(monkeypatch):
    monkeypatch.setattr(GmailMailbox, "_get", lambda self, url, params=None: {"messages": []})
    assert (
        GmailMailbox(store=None, workspace_id="w1").recent_messages(days=90, max_messages=10) == []
    )
