"""Stripe webhook endpoint. Verifies the signature (when
CAREEROS_STRIPE_WEBHOOK_SECRET is set) and activates the paid plan."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Request, status

from careeros_api.dependencies import get_store
from careeros_api.schemas import MessageResponse
from careeros_api.stripe_webhook import (
    WebhookError,
    activate_from_event,
    now_seconds,
    parse_event,
    verify_signature,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe", response_model=MessageResponse)
async def stripe_webhook(request: Request) -> MessageResponse:
    payload = await request.body()
    secret = os.environ.get("CAREEROS_STRIPE_WEBHOOK_SECRET")
    if secret:
        try:
            verify_signature(
                payload,
                request.headers.get("stripe-signature"),
                secret,
                now=now_seconds(),
            )
        except WebhookError as error:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    try:
        outcome = activate_from_event(get_store(), parse_event(payload))
    except WebhookError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    return MessageResponse(message=outcome)
