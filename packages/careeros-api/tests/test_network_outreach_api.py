"""CRM outreach drafter: draft grounded emails, send + log via Gmail."""

from __future__ import annotations


def _contact(client, headers, email="mentor@example.com"):
    r = client.post(
        "/contacts",
        headers=headers,
        json={
            "name": "Priya Rao",
            "role": "hiring_manager",
            "organization_name": "Ramp",
            "email": email,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _brain(client, headers):
    client.post(
        "/brain", headers=headers, json={"full_name": "Sahil Sachdeva", "email": "s@example.com"}
    )


def test_draft_intro_is_grounded(client, auth_headers):
    headers = auth_headers()
    _brain(client, headers)
    cid = _contact(client, headers)
    r = client.post(f"/contacts/{cid}/outreach", headers=headers, json={"kind": "intro"})
    assert r.status_code == 200
    body = r.json()
    assert "Priya" in body["body"]  # addresses the contact
    assert "Sahil Sachdeva" in body["body"]  # signs with the real name
    assert body["sent"] is False and body["ai_used"] is False


def test_referral_uses_target_role(client, auth_headers):
    headers = auth_headers()
    _brain(client, headers)
    cid = _contact(client, headers)
    r = client.post(
        f"/contacts/{cid}/outreach",
        headers=headers,
        json={"kind": "referral", "target_role": "Growth Lead"},
    )
    assert "Growth Lead" in r.json()["subject"]


def test_bad_kind_is_422(client, auth_headers):
    headers = auth_headers()
    cid = _contact(client, headers)
    r = client.post(f"/contacts/{cid}/outreach", headers=headers, json={"kind": "nope"})
    assert r.status_code == 422


def test_unknown_contact_is_404(client, auth_headers):
    r = client.post("/contacts/nope/outreach", headers=auth_headers(), json={"kind": "intro"})
    assert r.status_code == 404


def test_send_without_google_degrades_gracefully(client, auth_headers):
    headers = auth_headers()
    _brain(client, headers)
    cid = _contact(client, headers)
    r = client.post(
        f"/contacts/{cid}/outreach", headers=headers, json={"kind": "intro", "send": True}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["sent"] is False and body["logged"] is False
    assert "Google" in body["reason"]


def test_send_without_email_is_reported(client, auth_headers):
    headers = auth_headers()
    _brain(client, headers)
    cid = _contact(client, headers, email=None)
    r = client.post(
        f"/contacts/{cid}/outreach", headers=headers, json={"kind": "intro", "send": True}
    )
    assert r.json()["reason"] == "this contact has no email address"
