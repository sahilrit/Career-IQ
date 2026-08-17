"""Tests for Stripe webhook signature verification and plan activation."""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest

from careeros_api import dependencies
from careeros_api.stripe_webhook import (
    WebhookError,
    activate_from_event,
    verify_signature,
)
from careeros_billing import SubscriptionRepository
from careeros_billing.plan import PlanTier
from careeros_tenancy import TenancyRepository


def _completed_event(email="ada@example.com", plan="pro"):
    return {
        "type": "checkout.session.completed",
        "data": {"object": {"customer_email": email, "metadata": {"plan": plan}}},
    }


def _workspace_id_for(store, email):
    tenancy = TenancyRepository(store)
    user = tenancy.find_user_by_email(email)
    return tenancy.workspaces_for_user(user.id)[0].workspace_id


def test_activation_sets_plan(client, auth_headers):
    auth_headers()  # signs up ada@example.com (Free by default)
    store = dependencies.get_store()
    outcome = activate_from_event(store, _completed_event(plan="pro"))
    assert "activated pro" in outcome
    workspace_id = _workspace_id_for(store, "ada@example.com")
    assert SubscriptionRepository(store).load_or_none(workspace_id).plan_tier == PlanTier.PRO


def test_activation_infers_tier_from_amount(client, auth_headers):
    auth_headers()
    store = dependencies.get_store()
    event = {
        "type": "checkout.session.completed",
        "data": {"object": {"customer_email": "ada@example.com", "amount_total": 9900}},
    }
    activate_from_event(store, event)
    workspace_id = _workspace_id_for(store, "ada@example.com")
    assert SubscriptionRepository(store).load_or_none(workspace_id).plan_tier == PlanTier.AGENCY


def test_activation_unknown_email_raises(client):
    with pytest.raises(WebhookError):
        activate_from_event(dependencies.get_store(), _completed_event(email="nobody@example.com"))


def test_non_checkout_event_is_ignored(client):
    outcome = activate_from_event(dependencies.get_store(), {"type": "invoice.paid"})
    assert "ignored" in outcome


def test_signature_verification_roundtrip():
    secret = "whsec_test"
    payload = json.dumps(_completed_event()).encode()
    timestamp = 1_700_000_000
    signed = f"{timestamp}.".encode() + payload
    signature = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    header = f"t={timestamp},v1={signature}"
    verify_signature(payload, header, secret, now=timestamp)  # no raise


def test_signature_mismatch_raises():
    with pytest.raises(WebhookError):
        verify_signature(b"{}", "t=1700000000,v1=deadbeef", "whsec_test", now=1_700_000_000)


def test_webhook_endpoint_fails_closed_without_secret(client, auth_headers):
    """Previously this endpoint activated plans with no signature when the
    secret was unset (a fail-open auth bypass). It must now refuse (503)."""
    auth_headers()
    response = client.post("/webhooks/stripe", json=_completed_event(plan="agency"))
    assert response.status_code == 503
    assert response.json()["detail"] != "activated agency for ada@example.com"


# --- Regression: signature still enforced when the secret IS set --------------


def test_stripe_endpoint_rejects_bad_signature_when_secret_set(client, auth_headers, monkeypatch):
    auth_headers()  # register ada@example.com
    monkeypatch.setenv("CAREEROS_STRIPE_WEBHOOK_SECRET", "whsec_test")
    response = client.post(
        "/webhooks/stripe",
        headers={"stripe-signature": "t=1700000000,v1=deadbeef"},
        json={"type": "checkout.session.completed", "data": {"object": {}}},
    )
    assert response.status_code == 400
