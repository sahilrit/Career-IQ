"""Opportunity endpoints: run a job search (discover + qualify) and
generate an application package for a specific posting.

The heavy provider wiring lives in ``careeros_job_search`` (shared with
the dashboard). Both entry points are referenced at module level so
tests can patch them without touching the real network.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from careeros_ai import AIError
from careeros_api import ai_support
from careeros_api.dependencies import Context
from careeros_api.schemas import (
    ApplicationPackageResponse,
    GenerateRequest,
    SearchRequest,
    SearchResponse,
)
from careeros_career_brain import CareerBrainRepository
from careeros_job_search import generate_application_for_job, search_for_jobs
from careeros_tenancy import Permission

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


def _identity_id(context: Context) -> str:
    brains = CareerBrainRepository(context.store).list_all()
    if not brains:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "create a Career Brain first")
    return brains[0].identity.id


@router.post("/search", response_model=SearchResponse)
def search(body: SearchRequest, context: Context) -> SearchResponse:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    summary = search_for_jobs(
        context.store,
        _identity_id(context),
        keywords=body.keywords,
        remote_only=body.remote_only,
        limit=body.limit,
    )
    return SearchResponse(discovered=summary["discovered"], qualified=summary["qualified"])


@router.post("/generate", response_model=ApplicationPackageResponse)
def generate(body: GenerateRequest, context: Context) -> ApplicationPackageResponse:
    identity_id = _identity_id(context)
    generator = ai_support.resolve_cover_letter_generator(
        context.store, context.account.workspace_id
    )
    ai_used = generator is not None
    ai_error: str | None = None
    try:
        package = generate_application_for_job(
            context.store, identity_id, body.job_url, cover_letter_generator=generator
        )
    except AIError as error:
        # A transient AI failure (bad key, quota, timeout) never blocks
        # generation — fall back to the free template, but surface why.
        package = generate_application_for_job(context.store, identity_id, body.job_url)
        ai_used = False
        ai_error = str(error)
    if package is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "that posting is no longer available to generate from",
        )
    return ApplicationPackageResponse(
        resume_text=package.resume_text,
        cover_letter=package.cover_letter,
        ai_used=ai_used,
        ai_error=ai_error,
    )
