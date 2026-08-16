"""Stripe webhook handling — signature verification and plan activation,
stdlib only (no Stripe SDK, honoring the zero-paid-dependency rule).

On ``checkout.session.completed`` we read the customer email and the
plan (from the session's ``metadata.plan``, or inferred from
``amount_total``), find that user's workspace, and set its subscription
tier. This replaces the manual Admin-page activation step.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

from careeros_billing import Subscription, SubscriptionRepository
from careeros_billing.plan import PlanTier
from careeros_common import DocumentStore
from careeros_tenancy import TenancyRepository

_SIGNATURE_TOLERANCE_SECONDS = 300
# Amount (in cents) -> tier, a fallback when metadata.plan is absent.
_AMOUNT_TO_TIER = {2900: PlanTier.PRO, 9900: PlanTier.AGENCY}


class WebhookError(Exception):
    """Raised when a webhook can't be verified or processed."""


def verify_signature(
    payload: bytes, signature_header: str | None, secret: str, *, now: float
) -> None:
    """Verify Stripe's ``Stripe-Signature`` header. Raises WebhookError on
    any mismatch. Implements Stripe's scheme with stdlib hmac."""
    if not signature_header:
        raise WebhookError("missing signature header")
    parts = dict(item.split("=", 1) for item in signature_header.split(",") if "=" in item)
    timestamp = parts.get("t")
    provided = parts.get("v1")
    if not timestamp or not provided:
        raise WebhookError("malformed signature header")
    if abs(now - int(timestamp)) > _SIGNATURE_TOLERANCE_SECONDS:
        raise WebhookError("signature timestamp outside tolerance")
    signed_payload = f"{timestamp}.".encode() + payload
    expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, provided):
        raise WebhookError("signature mismatch")


def _tier_from_session(session: dict[str, Any]) -> PlanTier | None:
    plan = (session.get("metadata") or {}).get("plan")
    if plan:
        try:
            return PlanTier(plan.lower())
        except ValueError:
            return None
    amount = session.get("amount_total")
    return _AMOUNT_TO_TIER.get(amount) if amount is not None else None


def activate_from_event(store: DocumentStore, event: dict[str, Any]) -> str:
    """Apply a parsed Stripe event. Returns a human-readable outcome."""
    if event.get("type") != "checkout.session.completed":
        return f"ignored event type {event.get('type')}"
    session = (event.get("data") or {}).get("object") or {}
    email = (
        (
            session.get("customer_email")
            or (session.get("customer_details") or {}).get("email")
            or ""
        )
        .strip()
        .lower()
    )
    if not email:
        raise WebhookError("event has no customer email")
    tier = _tier_from_session(session)
    if tier is None:
        raise WebhookError("could not determine plan tier from event")

    tenancy = TenancyRepository(store)
    user = tenancy.find_user_by_email(email)
    if user is None:
        raise WebhookError(f"no account for {email}")
    memberships = tenancy.workspaces_for_user(user.id)
    if not memberships:
        raise WebhookError(f"{email} has no workspace")
    workspace_id = memberships[0].workspace_id

    subscriptions = SubscriptionRepository(store)
    subscription = subscriptions.load_or_none(workspace_id) or Subscription(
        workspace_id=workspace_id, plan_tier=tier
    )
    subscription.plan_tier = tier
    subscriptions.save(subscription)
    return f"activated {tier.value} for {email}"


def parse_event(payload: bytes) -> dict[str, Any]:
    try:
        return json.loads(payload)
    except json.JSONDecodeError as error:
        raise WebhookError("invalid JSON payload") from error


def now_seconds() -> float:
    return time.time()
