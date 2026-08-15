"""Shared fixtures for Arbeitnow provider tests. No real network calls."""

from __future__ import annotations

from typing import Any

import pytest

# A representative slice of Arbeitnow's real /api/job-board-api response
# shape: {"data": [...], "links": {...}, "meta": {...}}.
ARBEITNOW_FIXTURE: list[dict[str, Any]] = [
    {
        "slug": "senior-backend-engineer-acme",
        "company_name": "Acme Corp",
        "title": "Senior Backend Engineer",
        "description": "We need a senior backend engineer for our Python/Django stack.",
        "remote": True,
        "url": "https://www.arbeitnow.com/jobs/senior-backend-engineer-acme",
        "tags": ["python", "django", "postgres"],
        "job_types": ["Full time"],
        "location": "Worldwide",
        "created_at": 1785600000,
    },
    {
        "slug": "frontend-engineer-widgetco",
        "company_name": "WidgetCo",
        "title": "Frontend Engineer",
        "description": "React + TypeScript, on-site only.",
        "remote": False,
        "url": "https://www.arbeitnow.com/jobs/frontend-engineer-widgetco",
        "tags": ["react", "typescript"],
        "job_types": ["Contract"],
        "location": "Berlin, Germany",
        "created_at": 1785945600,
    },
]


class FakeTransport:
    def __init__(
        self, entries: list[dict[str, Any]] | None = None, *, raise_error: Exception | None = None
    ) -> None:
        self._entries = entries if entries is not None else ARBEITNOW_FIXTURE
        self._raise_error = raise_error
        self.fetch_calls = 0

    def fetch(self) -> list[dict[str, Any]]:
        self.fetch_calls += 1
        if self._raise_error is not None:
            raise self._raise_error
        return self._entries


@pytest.fixture
def arbeitnow_fixture() -> list[dict[str, Any]]:
    return ARBEITNOW_FIXTURE


@pytest.fixture
def fake_transport_cls() -> type[FakeTransport]:
    return FakeTransport
