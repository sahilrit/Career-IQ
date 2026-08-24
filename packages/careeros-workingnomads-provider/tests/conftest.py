"""Shared fixtures for Working Nomads provider tests. No real network calls.

The documents below match the ``_source`` shape returned by Working Nomads'
search backend, captured 2026-08-24.
"""

from __future__ import annotations

from typing import Any

import pytest

SEARCH_DOCS: list[dict[str, Any]] = [
    {
        "id": 1752874,
        "title": "Marketing Associate",
        "slug": "marketing-associate-reflex-media-inc-1752874",
        "company": "Reflex Media, Inc.",
        "category_name": "Marketing",
        "description": (
            "<p>MARKETING ASSOCIATE&nbsp;(Entry-Level)</p><p>Run <b>PPC</b> campaigns.</p>"
        ),
        "position_type": "ft",
        "tags": ["seo", "advertising", "google analytics"],
        "locations": ["USA"],
        "pub_date": "2026-07-25T14:33:12.458737-04:00",
        "apply_url": "https://reflexmediainc.applytojob.com/apply/uTEp2lGf4Y/Marketing-Associate",
        "salary_range": "$55k-$65k per year",
        "annual_salary_usd": 65000.0,
        "experience_level": "ENTRY_LEVEL",
        "expired": False,
    },
    {
        "id": 1752999,
        "title": "Contract Plumbing Coordinator",
        "slug": "contract-plumbing-coordinator-widgetco-1752999",
        "company": "WidgetCo",
        "category_name": "Operations",
        "description": "<p>Coordinate plumbing crews.</p>",
        "position_type": "contract",
        "tags": ["operations"],
        "locations": ["Europe"],
        "pub_date": "2026-08-20T09:00:00+00:00",
        "salary_range": "",
        "annual_salary_usd": None,
        "expired": False,
    },
    {
        # Expired postings still come back from the index; we drop them.
        "id": 1700000,
        "title": "Stale Growth Lead",
        "slug": "stale-growth-lead-oldco-1700000",
        "company": "OldCo",
        "description": "<p>Long gone.</p>",
        "tags": [],
        "locations": ["Worldwide"],
        "expired": True,
    },
]


class FakeTransport:
    """Replays canned Elasticsearch ``_source`` documents."""

    def __init__(
        self,
        docs: list[dict[str, Any]] | None = None,
        *,
        raise_error: Exception | None = None,
    ) -> None:
        self._docs = docs if docs is not None else SEARCH_DOCS
        self._raise_error = raise_error
        self.search_calls: list[dict[str, Any]] = []

    def search(self, *, keywords: list[str], size: int) -> list[dict[str, Any]]:
        if self._raise_error is not None:
            raise self._raise_error
        self.search_calls.append({"keywords": list(keywords), "size": size})
        return self._docs


@pytest.fixture
def search_docs() -> list[dict[str, Any]]:
    return SEARCH_DOCS


@pytest.fixture
def fake_transport_cls() -> type[FakeTransport]:
    return FakeTransport
