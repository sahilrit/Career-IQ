"""Account lifecycle — GDPR data export and account deletion."""

from __future__ import annotations

PASSWORD = "Very-Secure-Password-1!"


def test_export_returns_account_and_data(client, auth_headers):
    headers = auth_headers()
    client.post("/brain", headers=headers, json={"full_name": "Ada", "email": "ada@example.com"})
    client.post("/brain/skills", headers=headers, json={"name": "Meta Ads"})

    response = client.get("/account/export", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-disposition"].endswith('filename="careeros-export.json"')
    body = response.json()
    assert body["account"]["email"] == "ada@example.com"
    assert body["account"]["workspace_id"]
    assert len(body["data"]) >= 1  # the Career Brain is in the export


def test_delete_account_purges_and_revokes(client, auth_headers):
    headers = auth_headers()
    client.post("/brain", headers=headers, json={"full_name": "Ada", "email": "ada@example.com"})
    client.post("/brain/skills", headers=headers, json={"name": "Meta Ads"})

    deleted = client.delete("/account", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    assert deleted.json()["documents_removed"] >= 1

    # session revoked, data gone, cannot log back in
    assert client.get("/brain", headers=headers).status_code == 401
    assert (
        client.post(
            "/auth/login", json={"email": "ada@example.com", "password": PASSWORD}
        ).status_code
        == 401
    )


def test_delete_is_tenant_scoped(client, auth_headers):
    a = auth_headers(email="a@example.com", full_name="A")
    b = auth_headers(email="b@example.com", full_name="B")
    client.post("/brain", headers=b, json={"full_name": "B", "email": "b@example.com"})
    client.delete("/account", headers=a)
    # B is untouched
    assert client.get("/brain", headers=b).status_code == 200


def test_account_requires_auth(client):
    assert client.get("/account/export").status_code == 401
    assert client.delete("/account").status_code == 401
