"""Contract tests for the audit pitch-kit endpoint (freelance money-maker)."""

from __future__ import annotations


def _brain(client, headers):
    client.post("/brain", headers=headers, json={"full_name": "Ada", "email": "ada@example.com"})


def test_pitch_kit_needs_a_brain(client, auth_headers):
    response = client.post(
        "/audit/pitch-kit", headers=auth_headers(), json={"company_name": "Acme"}
    )
    assert response.status_code == 404


def test_pitch_kit_full_deliverables(client, auth_headers):
    headers = auth_headers()
    _brain(client, headers)
    response = client.post(
        "/audit/pitch-kit",
        headers=headers,
        json={
            "company_name": "Acme Shop",
            "website": "acme.com",
            "industry": "ecommerce",
            "monthly_visitors": 50000,
            "conversion_rate": 0.02,
            "average_order_value": 60,
            "ads": [{"headline": "Buy now", "body_text": "Great stuff"}],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert {
        "findings",
        "roi",
        "email",
        "linkedin_message",
        "loom_script",
        "proposal",
        "ai_used",
        "pdf_base64",
    } <= set(body.keys())
    assert body["ai_used"] is False  # no key configured
    assert body["pdf_base64"]  # a PDF was produced
    assert body["roi"]["projected_additional_annual_revenue"] > 0


def test_pitch_kit_requires_auth(client):
    assert client.post("/audit/pitch-kit", json={"company_name": "x"}).status_code == 401
