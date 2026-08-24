"""Contract tests for the company-watchlist endpoints."""

from __future__ import annotations

from careeros_job_providers import JobPosting


def _posting(external_id: str) -> JobPosting:
    return JobPosting(
        source_provider="greenhouse",
        external_id=external_id,
        title="Growth Lead",
        company_name="Acme",
        url=f"https://boards.greenhouse.io/acme/jobs/{external_id}",
    )


def test_watchlist_requires_auth(client):
    assert client.get("/watchlist").status_code == 401


def test_watch_list_and_unwatch(client, auth_headers):
    headers = auth_headers()

    created = client.post(
        "/watchlist",
        headers=headers,
        json={"ats": "greenhouse", "board_token": "stripe", "display_name": "Stripe"},
    )
    assert created.status_code == 201

    listed = client.get("/watchlist", headers=headers).json()
    assert len(listed) == 1
    assert listed[0]["board_token"] == "stripe"

    removed = client.delete("/watchlist/greenhouse/stripe", headers=headers)
    assert removed.status_code == 200
    assert client.get("/watchlist", headers=headers).json() == []


def test_ats_options_lists_the_supported_systems(client, auth_headers):
    options = client.get("/watchlist/ats-options", headers=auth_headers()).json()
    assert set(options) == {"greenhouse", "lever", "ashby"}


def test_watchlists_are_isolated_between_workspaces(client, auth_headers):
    alice = auth_headers(email="alice@example.com")
    bob = auth_headers(email="bob@example.com")
    client.post(
        "/watchlist",
        headers=alice,
        json={"ats": "lever", "board_token": "acme"},
    )
    assert client.get("/watchlist", headers=bob).json() == []


def test_check_reports_new_postings(client, auth_headers, monkeypatch):
    headers = auth_headers()
    client.post("/watchlist", headers=headers, json={"ats": "greenhouse", "board_token": "acme"})

    boards = {"acme": [_posting("1")]}

    def fake_fetch(company):
        return boards.get(company.board_token, [])

    # Patch the board fetch the router's check_watchlist uses, so no network.
    from careeros_watchlist import boards as boards_module

    monkeypatch.setattr(boards_module, "fetch_board", fake_fetch)

    # First check baselines silently.
    first = client.post("/watchlist/check", headers=headers).json()
    assert first["new_postings"] == []
    assert first["baselined"] == 1

    boards["acme"] = [_posting("1"), _posting("2")]
    second = client.post("/watchlist/check", headers=headers).json()
    assert [p["external_id"] for p in second["new_postings"]] == ["2"]
