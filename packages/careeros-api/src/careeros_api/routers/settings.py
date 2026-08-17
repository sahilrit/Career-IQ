"""Workspace settings: the AI key + optional model powering AI features.
The key is write-only over the API — GET returns only whether one is set
and which model is active."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from careeros_api import ai_support
from careeros_api.dependencies import Context
from careeros_api.schemas import AiKeyRequest, AiStatusResponse
from careeros_tenancy import Permission


def _status(context: Context) -> AiStatusResponse:
    store, workspace_id = context.store, context.account.workspace_id
    return AiStatusResponse(
        has_key=ai_support.has_workspace_key(store, workspace_id),
        model=ai_support.model_label(store, workspace_id),
    )


router = APIRouter(tags=["settings"])


@router.get("/settings/ai", response_model=AiStatusResponse)
def get_ai(context: Context) -> AiStatusResponse:
    return _status(context)


@router.put("/settings/ai", response_model=AiStatusResponse)
def put_ai(body: AiKeyRequest, context: Context) -> AiStatusResponse:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    store, workspace_id = context.store, context.account.workspace_id
    key = body.api_key.strip()
    model = body.model.strip() or None

    if key:
        if not key.startswith("sk-") or len(key) < 20:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "that doesn't look like an API key — paste an 'sk-…' key from "
                "Anthropic (sk-ant-…), OpenRouter (sk-or-…), or OpenAI (sk-…)",
            )
        ai_support.store_workspace_key(store, workspace_id, key)
    elif not ai_support.has_workspace_key(store, workspace_id):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "add your API key first")

    # The model updates independently — you can change it without re-entering
    # the key. Empty clears it back to the provider default.
    ai_support.store_workspace_model(store, workspace_id, model)
    return _status(context)


@router.delete("/settings/ai", response_model=AiStatusResponse)
def delete_ai(context: Context) -> AiStatusResponse:
    context.require_permission(Permission.CAREER_BRAIN_WRITE)
    ai_support.delete_workspace_key(context.store, context.account.workspace_id)
    return _status(context)
