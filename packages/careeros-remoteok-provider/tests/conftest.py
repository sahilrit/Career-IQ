"""Shared fixtures for RemoteOK provider tests. No real network calls."""

from __future__ import annotations

from typing import Any

import pytest

# A representative slice of RemoteOK's real /api response shape: the feed
# always starts with a non-job legal/metadata object, followed by job
# entries.
REMOTEOK_FIXTURE: list[dict[str, Any]] = [
    {"legal": "https://remoteok.com/legal", "https://remoteok.com/api": "..."},
    {
        "id": "1000001",
        "slug": "senior-backend-engineer-acme",
        "company": "Acme Corp",
        "position": "Senior Backend Engineer",
        "tags": ["python", "django", "postgres"],
        "url": "https://remoteok.com/remote-jobs/1000001",
        "apply_url": "https://acme.example/careers/1000001",
        "date": "2026-08-01T09:00:00+00:00",
        "location": "Worldwide",
        "salary_min": 120000,
        "salary_max": 160000,
        "description": "We need a senior backend engineer for our Python/Django stack.",
    },
    {
        "id": "1000002",
        "slug": "frontend-engineer-widgetco",
        "company": "WidgetCo",
        "position": "Frontend Engineer",
        "tags": ["react", "typescript"],
        "url": "https://remoteok.com/remote-jobs/1000002",
        "date": "2026-08-05T09:00:00+00:00",
        "location": "US Only",
        "description": "React + TypeScript, no salary listed.",
    },
]


class FakeTransport:
    def __init__(
        self, entries: list[dict[str, Any]] | None = None, *, raise_error: Exception | None = None
    ) -> None:
        self._entries = entries if entries is not None else REMOTEOK_FIXTURE
        self._raise_error = raise_error
        self.fetch_calls = 0

    def fetch(self) -> list[dict[str, Any]]:
        self.fetch_calls += 1
        if self._raise_error is not None:
            raise self._raise_error
        return self._entries


@pytest.fixture
def remoteok_fixture() -> list[dict[str, Any]]:
    return REMOTEOK_FIXTURE


@pytest.fixture
def fake_transport_cls() -> type[FakeTransport]:
    return FakeTransport
