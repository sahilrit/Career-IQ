"""Review queue: applications the autopilot PREPARED (filled a real form for)
but left for a human to finish — the captcha-gated ones. The prepare-and-review
daemon run persists these; the React app lists them so you can open each form,
read the AI cover letter, apply, and mark it done.

Read straight from the tenant-scoped store (same as the autopilot router) to
keep the browser-heavy autopilot package out of the API image.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from careeros_api.dependencies import Context
from careeros_api.schemas import (
    MessageResponse,
    PreparedApplicationResponse,
    PreparedStatusRequest,
)

_ENTITY_TYPE = "prepared_application"

router = APIRouter(prefix="/review", tags=["review"])


def _to_response(record: dict[str, Any]) -> PreparedApplicationResponse:
    return PreparedApplicationResponse(
        id=str(record.get("id", "")),
        job_title=str(record.get("job_title", "?")),
        company_name=str(record.get("company_name", "?")),
        apply_url=str(record.get("apply_url", "")),
        cover_letter=str(record.get("cover_letter", "")),
        match_score=record.get("match_score"),
        prepared_at=str(record.get("prepared_at", "")),
    )


@router.get("/prepared", response_model=list[PreparedApplicationResponse])
def list_prepared(context: Context) -> list[PreparedApplicationResponse]:
    records = [
        record
        for record in context.store.list(_ENTITY_TYPE)
        if record.get("status", "pending") == "pending"
    ]
    records.sort(key=lambda record: record.get("prepared_at", ""), reverse=True)
    return [_to_response(record) for record in records]


@router.patch("/prepared/{prepared_id}", response_model=MessageResponse)
def update_status(
    prepared_id: str, body: PreparedStatusRequest, context: Context
) -> MessageResponse:
    record = context.store.get_or_none(_ENTITY_TYPE, prepared_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such prepared application")
    record["status"] = body.status
    context.store.put(_ENTITY_TYPE, prepared_id, record)
    return MessageResponse(message=f"marked {body.status}")
