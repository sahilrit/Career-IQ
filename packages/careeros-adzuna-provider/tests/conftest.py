"""Shared fixtures for Adzuna provider tests. No real network calls.

Result shape matches Adzuna's documented ``/v1/api/jobs/{country}/search/{page}``
response.
"""

from __future__ import annotations

from typing import Any

import pytest

RESULT_SALARIED: dict[str, Any] = {
    "id": "4200001",
    "title": "Performance <strong>Marketing</strong> Manager",
    "description": "Own paid acquisition across Google and Meta. Report to the CMO…",
    "created": "2026-08-12T09:14:22Z",
    "redirect_url": "https://www.adzuna.co.uk/details/4200001",
    "company": {"display_name": "Acme Corp"},
    "location": {"display_name": "London, UK", "area": ["UK", "London"]},
    "salary_min": 55000.0,
    "salary_max": 70000.0,
    "salary_is_predicted": "0",
    "contract_time": "full_time",
    "contract_type": "permanent",
    "category": {"label": "PR, Advertising & Marketing Jobs", "tag": "pr-advertising-marketing"},
}

RESULT_PREDICTED_SALARY: dict[str, Any] = {
    "id": "4200002",
    "title": "Growth Lead (Remote)",
    "description": "Fully remote growth role.",
    "created": "2026-08-20T11:00:00Z",
    "redirect_url": "https://www.adzuna.co.uk/details/4200002",
    "company": {"display_name": "WidgetCo"},
    "location": {"display_name": "Remote", "area": ["UK"]},
    "salary_min": 60000.0,
    "salary_max": 60000.0,
    # Adzuna guesses a salary when the advert has none. Treating a guess as a
    # stated figure would let it silently pass the user's salary floor.
    "salary_is_predicted": "1",
    "contract_time": "part_time",
    "category": {"label": "IT Jobs"},
}

RESULT_MINIMAL: dict[str, Any] = {
    "id": "4200003",
    "title": "Coordinator",
    "redirect_url": "https://www.adzuna.co.uk/details/4200003",
}

RESULT_UNUSABLE: dict[str, Any] = {"title": "No id and no link"}


class FakeTransport:
    def __init__(
        self,
        pages: list[list[dict[str, Any]]] | None = None,
        *,
        raise_error: Exception | None = None,
    ) -> None:
        self._pages = (
            pages
            if pages is not None
            else [[RESULT_SALARIED, RESULT_PREDICTED_SALARY, RESULT_MINIMAL, RESULT_UNUSABLE], []]
        )
        self._raise_error = raise_error
        self.calls: list[dict[str, Any]] = []

    def search(
        self,
        *,
        country: str,
        page: int,
        what: str,
        where: str | None,
        results_per_page: int,
        max_days_old: int | None = None,
    ) -> list[dict[str, Any]]:
        if self._raise_error is not None:
            raise self._raise_error
        self.calls.append(
            {
                "country": country,
                "page": page,
                "what": what,
                "where": where,
                "results_per_page": results_per_page,
                "max_days_old": max_days_old,
            }
        )
        index = len(self.calls) - 1
        return self._pages[index] if index < len(self._pages) else []


@pytest.fixture
def result_salaried() -> dict[str, Any]:
    return RESULT_SALARIED


@pytest.fixture
def result_predicted() -> dict[str, Any]:
    return RESULT_PREDICTED_SALARY


@pytest.fixture
def result_minimal() -> dict[str, Any]:
    return RESULT_MINIMAL


@pytest.fixture
def fake_transport_cls() -> type[FakeTransport]:
    return FakeTransport
