"""Saved searches with a new-match digest. Save a search, then 'run' it to get
only the qualified matches discovered since last time — optionally emailed."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from careeros_api import email as email_module
from careeros_api.dependencies import Context
from careeros_api.saved_search_store import SavedSearch, SavedSearchRepository
from careeros_career_brain import CareerBrainRepository
from careeros_job_search import search_for_jobs
from careeros_tenancy import Permission

router = APIRouter(prefix="/saved-searches", tags=["saved-searches"])

_DIGEST_LIMIT = 10


class SavedSearchRequest(BaseModel):
    keywords: list[str] = Field(min_length=1)
    remote_only: bool = True


class RunRequest(BaseModel):
    send_email: bool = False


def _identity_id(context: Context) -> str:
    brains = CareerBrainRepository(context.store).list_all()
    if not brains:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "create a Career Brain first")
    return brains[0].identity.id


@router.get("")
def list_searches(context: Context) -> list[dict[str, Any]]:
    return [s.model_dump(mode="json") for s in SavedSearchRepository(context.store).list_all()]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_search(body: SavedSearchRequest, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    keywords = [k.strip() for k in body.keywords if k.strip()]
    if not keywords:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "add at least one keyword")
    search = SavedSearch(keywords=keywords, remote_only=body.remote_only)
    SavedSearchRepository(context.store).save(search)
    return search.model_dump(mode="json")


@router.delete("/{search_id}")
def delete_search(search_id: str, context: Context) -> dict[str, bool]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    SavedSearchRepository(context.store).delete(search_id)
    return {"deleted": True}


@router.post("/{search_id}/run")
def run_search(search_id: str, body: RunRequest, context: Context) -> dict[str, Any]:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    repo = SavedSearchRepository(context.store)
    search = repo.get_or_none(search_id)
    if search is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "saved search not found")
    identity_id = _identity_id(context)

    # Discover (adds only genuinely new postings to the brain — deduped by URL).
    search_for_jobs(
        context.store,
        identity_id,
        keywords=search.keywords,
        remote_only=search.remote_only,
        limit=50,
    )

    applications = [
        application
        for brain in CareerBrainRepository(context.store).list_all()
        for application in brain.applications
    ]
    seen = set(search.seen_application_ids)
    new_matches = sorted(
        (a for a in applications if a.id not in seen),
        key=lambda a: a.match_score or 0,
        reverse=True,
    )

    # Everything is now "seen" for the next digest.
    search.seen_application_ids = [a.id for a in applications]
    repo.save(search)

    emailed = False
    if body.send_email and new_matches:
        plural = "es" if len(new_matches) != 1 else ""
        subject = f"{len(new_matches)} new match{plural} for your search"
        lines = [
            f"- {a.job_title} at {a.company_name}"
            + (f" ({round((a.match_score or 0) * 100)}% match)" if a.match_score else "")
            + (f"\n  {a.job_url}" if a.job_url else "")
            for a in new_matches[:_DIGEST_LIMIT]
        ]
        emailed = email_module.send_email(
            to=context.account.user.email,
            subject=subject,
            body="New matches since your last check:\n\n" + "\n".join(lines),
        )

    return {
        "new_count": len(new_matches),
        "new_matches": [a.model_dump(mode="json") for a in new_matches[:_DIGEST_LIMIT]],
        "emailed": emailed,
        "email_configured": email_module.smtp_configured(),
    }
