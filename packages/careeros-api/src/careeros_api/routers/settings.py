"""Workspace settings: the Anthropic API key powering AI features. The key
is write-only over the API — GET returns only whether one is set."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from careeros_api import ai_support
from careeros_api.dependencies import Context
from careeros_api.schemas import AiKeyRequest, AiStatusResponse
from careeros_tenancy import Permission

router = APIRouter(tags=["settings"])


@router.get("/settings/ai", response_model=AiStatusResponse)
def get_ai(context: Context) -> AiStatusResponse:
    return AiStatusResponse(
        has_key=ai_support.has_workspace_key(context.store, context.account.workspace_id),
        model=ai_support.ai_model(),
    )


@router.put("/settings/ai", response_model=AiStatusResponse)
def put_ai(body: AiKeyRequest, context: Context) -> AiStatusResponse:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    key = body.api_key.strip()
    if not key.startswith("sk-") or len(key) < 20:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "that doesn't look like an API key — paste an 'sk-…' key from "
            "Anthropic (sk-ant-…), OpenRouter (sk-or-…), or OpenAI (sk-…)",
        )
    ai_support.store_workspace_key(context.store, context.account.workspace_id, key)
    return AiStatusResponse(has_key=True, model=ai_support.ai_model())


@router.delete("/settings/ai", response_model=AiStatusResponse)
def delete_ai(context: Context) -> AiStatusResponse:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    ai_support.delete_workspace_key(context.store, context.account.workspace_id)
    return AiStatusResponse(has_key=False, model=ai_support.ai_model())
