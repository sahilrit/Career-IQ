"""Shared fixtures for Seek provider tests. No real network.

Row shapes mirror Seek's own public search API response
(``/api/jobsearch/v5/search``) — field names verified against a live,
working response captured 2026-08-26.
"""

from __future__ import annotations

from typing import Any

import pytest

ROW_FULL: dict[str, Any] = {
    "id": "94152491",
    "title": "Marketing & Studio Assistant - Part Time",
    "companyName": "Viabrand",
    "teaser": "Join a boutique agency where your contribution matters.",
    "salaryLabel": "$28 - $32 per hour",
    "listingDate": "2026-08-23T23:05:13Z",
    "locations": [{"label": "Brisbane QLD", "countryCode": "AU"}],
    "workTypes": ["Part time"],
    "classifications": [
        {
            "classification": {"description": "Marketing & Communications"},
            "subclassification": {"description": "Marketing Assistants/Coordinators"},
        }
    ],
}

ROW_MINIMAL: dict[str, Any] = {
    "id": "94166166",
    "title": "Remote Growth Marketer",
    "companyName": "Widget Co",
    "listingDate": "2026-08-24T10:00:00Z",
    "locations": [{"label": "Remote", "countryCode": "AU"}],
}

ROW_UNUSABLE: dict[str, Any] = {"companyName": "No id or title"}

SEARCH_RESPONSE_BODY = (
    '{"totalCount": 2, "data": ['
    '{"id": "1", "title": "A", "companyName": "X"},'
    '{"id": "2", "title": "B", "companyName": "Y"}'
    "]}"
)


@pytest.fixture
def row_full() -> dict[str, Any]:
    return ROW_FULL


@pytest.fixture
def row_minimal() -> dict[str, Any]:
    return ROW_MINIMAL


@pytest.fixture
def row_unusable() -> dict[str, Any]:
    return ROW_UNUSABLE


@pytest.fixture
def search_response_body() -> str:
    return SEARCH_RESPONSE_BODY
