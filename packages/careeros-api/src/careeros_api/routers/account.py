"""Account lifecycle — data export (GDPR Art. 20 portability) and account
deletion (Art. 17 erasure). Both operate only on the authenticated caller's own
account and workspace data."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from careeros_api.dependencies import Context, get_auth_service

router = APIRouter(tags=["account"])


@router.get("/account/export")
def export_account(context: Context) -> JSONResponse:
    """Download everything CareerOS holds for this account — identity plus all
    tenant-scoped data — as a JSON file the user can keep."""
    account = context.account
    payload: dict[str, Any] = {
        "account": {
            "user_id": account.user.id,
            "email": account.user.email,
            "full_name": getattr(account.user, "full_name", None),
            "workspace_id": account.workspace_id,
            "role": getattr(account.role, "value", str(account.role)),
        },
        "data": context.store.export_all(),
    }
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": 'attachment; filename="careeros-export.json"'},
    )


@router.delete("/account")
def delete_account(context: Context) -> dict[str, Any]:
    """Permanently delete the caller's account: purge all workspace data, then
    remove the identity, sessions, and memberships. Irreversible. Auth is
    enforced by the Context dependency, so this only ever deletes the caller."""
    documents_removed = context.store.purge()
    get_auth_service().delete_account(context.account.user.id)
    return {
        "deleted": True,
        "documents_removed": documents_removed,
        "message": "Your account and all associated data have been deleted.",
    }
