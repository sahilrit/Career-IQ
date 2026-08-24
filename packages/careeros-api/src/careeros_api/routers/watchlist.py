"""Company-watchlist endpoints: watch a company's ATS board, list what's
watched, and check for newly-posted roles.

The heavy lifting lives in ``careeros_watchlist``; this is per-workspace
persistence plus the check trigger.
"""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from careeros_api.dependencies import Context
from careeros_event_bus import EventBus
from careeros_watchlist import ATS, WatchlistRepository, check_watchlist

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class WatchRequest(BaseModel):
    ats: ATS
    board_token: str = Field(min_length=1)
    display_name: str = ""


@router.get("")
def list_watched(context: Context) -> list[dict]:
    watched = WatchlistRepository(context.store).list_watched()
    return [company.model_dump(mode="json") for company in watched]


@router.post("", status_code=status.HTTP_201_CREATED)
def watch(body: WatchRequest, context: Context) -> dict:
    company = WatchlistRepository(context.store).watch(
        body.ats, body.board_token.strip(), display_name=body.display_name.strip()
    )
    return company.model_dump(mode="json")


@router.delete("/{ats}/{board_token}")
def unwatch(ats: ATS, board_token: str, context: Context) -> dict[str, bool]:
    WatchlistRepository(context.store).unwatch(ats, board_token)
    return {"removed": True}


@router.post("/check")
def check(context: Context) -> dict:
    result = check_watchlist(context.store, event_bus=EventBus())
    payload = result.model_dump(mode="json")
    # Trim the postings to what a board card needs.
    payload["new_postings"] = [
        {
            "external_id": p.external_id,
            "title": p.title,
            "company_name": p.company_name,
            "url": p.url,
        }
        for p in result.new_postings
    ]
    return payload


@router.get("/ats-options")
def ats_options() -> list[str]:
    return [ats.value for ats in ATS]
