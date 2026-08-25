"""UK Visa Jobs credentials: the user's own my.ukvisajobs.com email/password,
stored encrypted in the workspace's vault so the local autopilot daemon can
log in on their behalf. Same pattern as ``integrations_google.py``'s stored
OAuth connection, adapted for a plain login instead of a token exchange —
UK Visa Jobs has no OAuth to connect through."""

from __future__ import annotations

import json
from typing import Any

from careeros_api.vault_support import open_vault

_SERVICE = "ukvisajobs"
_REQUESTER = "careeros-app"


def store_credentials(store: Any, workspace_id: str, email: str, password: str) -> None:
    payload = json.dumps({"email": email, "password": password})
    open_vault(store, _SERVICE).store_secret(
        workspace_id, _SERVICE, payload, requester_id=_REQUESTER
    )


def has_credentials(store: Any, workspace_id: str) -> bool:
    return open_vault(store, _SERVICE).has_secret(workspace_id, _SERVICE)


def credentials(store: Any, workspace_id: str) -> tuple[str, str] | None:
    vault = open_vault(store, _SERVICE)
    if not vault.has_secret(workspace_id, _SERVICE):
        return None
    raw = vault.get_secret(workspace_id, _SERVICE, requester_id=_REQUESTER)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    email, password = parsed.get("email"), parsed.get("password")
    if not email or not password:
        return None
    return (email, password)


def delete_credentials(store: Any, workspace_id: str) -> None:
    vault = open_vault(store, _SERVICE)
    if vault.has_secret(workspace_id, _SERVICE):
        vault.delete_secret(workspace_id, _SERVICE, requester_id=_REQUESTER)
