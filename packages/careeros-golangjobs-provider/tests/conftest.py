"""Shared fixtures for Golang Jobs provider tests. No real network calls.

Rows mirror the golangjobs.tech Supabase `jobs` table shape captured
2026-08-24: id, title, company, type, description, salary_*,
application_url, slug, is_archived, posted_at.
"""

from __future__ import annotations

from typing import Any

import pytest

ROWS: list[dict[str, Any]] = [
    {
        "id": "f1410a66-804e-43e5-a3c5-387d2b10d387",
        "title": "Senior Backend Engineer (Go)",
        "company": "Okta",
        "type": "full-time",
        "description": "Build distributed systems in Go. Remote within the US.",
        "requirements": ["Go", "gRPC"],
        "salary_min": 150000,
        "salary_max": 190000,
        "salary_currency": "USD",
        "posted_at": "2026-08-20T15:09:40.236207+00:00",
        "application_url": "https://okta.example/apply/1",
        "slug": "senior-backend-engineer-go-at-okta-f1410a66",
        "is_archived": False,
    },
    {
        "id": "a2410a66-804e-43e5-a3c5-387d2b10d999",
        "title": "Go Developer",
        "company": "Encora",
        "type": "contract",
        "description": "Onsite in Berlin.",
        "requirements": [],
        "salary_min": None,
        "salary_max": None,
        "salary_currency": "EUR",
        "posted_at": "2026-08-18T10:00:00+00:00",
        "application_url": None,
        "slug": "go-developer-at-encora-a2410a66",
        "is_archived": False,
    },
    {
        "id": "deadbeef-0000-0000-0000-000000000000",
        "title": "Archived Role",
        "company": "OldCo",
        "type": "full-time",
        "description": "should never appear",
        "requirements": [],
        "salary_min": None,
        "salary_max": None,
        "salary_currency": "USD",
        "posted_at": "2025-01-01T00:00:00+00:00",
        "application_url": "https://oldco.example/1",
        "slug": "archived-role-at-oldco-deadbeef",
        "is_archived": True,
    },
]


class FakeTransport:
    """Replays canned rows and records the query params it was asked for."""

    def __init__(
        self, rows: list[dict[str, Any]] | None = None, *, raise_error: Exception | None = None
    ) -> None:
        self._rows = rows if rows is not None else [r for r in ROWS if not r["is_archived"]]
        self._raise_error = raise_error
        self.calls: list[dict[str, str]] = []

    def fetch(self, params: dict[str, str]) -> list[dict[str, Any]]:
        if self._raise_error is not None:
            raise self._raise_error
        self.calls.append(params)
        return list(self._rows)


@pytest.fixture
def rows() -> list[dict[str, Any]]:
    return ROWS


@pytest.fixture
def fake_transport_cls() -> type[FakeTransport]:
    return FakeTransport
