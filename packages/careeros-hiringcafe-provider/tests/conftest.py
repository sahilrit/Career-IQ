"""Shared fixtures for Hiring Cafe provider tests. No real network calls.

The hit shape below matches ``props.pageProps.ssrHits[n]`` from a real
response, captured 2026-08-24.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

HIT_REMOTE: dict[str, Any] = {
    "id": "greenhouse___acme___4400001",
    "source": "greenhouse",
    "apply_url": "https://boards.greenhouse.io/acme/jobs/4400001",
    "requisition_id": "4400001",
    "is_expired": False,
    "job_information": {"title": "Performance Marketing Manager"},
    "v5_processed_job_data": {
        "core_job_title": "Performance Marketing Manager",
        "company_name": "Acme Corp",
        "formatted_workplace_location": "Remote, United States",
        "workplace_type": "Remote",
        "yearly_min_compensation": 120000,
        "yearly_max_compensation": 150000,
        "listed_compensation_currency": "USD",
        "listed_compensation_frequency": "Yearly",
        "commitment": ["Full Time"],
        "seniority_level": "Senior Level",
        "job_category": "Marketing",
        "technical_tools": ["Google Ads", "Meta Ads Manager", "Looker"],
        "requirements_summary": "5+ years running paid acquisition across Google and Meta.",
        "role_activities": ["owning budget", "building dashboards"],
        "estimated_publish_date": "2026-07-24T00:00:00.000Z",
    },
}

HIT_ONSITE: dict[str, Any] = {
    "id": "zohorecruit___prop___93469000001728336",
    "source": "zohorecruit",
    "apply_url": "https://propsolutions4u.zohorecruit.in/jobs/Careers/93469000001728336/Perf",
    "requisition_id": "93469000001728336",
    "is_expired": False,
    "job_information": {"title": "Performance Marketing"},
    "v5_processed_job_data": {
        "company_name": "Prop Solutions 4U",
        "formatted_workplace_location": "Turbhe, Maharashtra, India",
        "workplace_type": "Onsite",
        "yearly_min_compensation": None,
        "yearly_max_compensation": None,
        "listed_compensation_currency": "INR",
        "commitment": ["Internship"],
        "job_category": "Marketing",
        "technical_tools": ["Canva"],
        "requirements_summary": "Bachelor's degree required; 4+ years in real estate marketing.",
        "role_activities": ["setting campaigns"],
    },
}

HIT_EXPIRED: dict[str, Any] = {
    "id": "lever___oldco___1",
    "apply_url": "https://jobs.lever.co/oldco/1",
    "is_expired": True,
    "job_information": {"title": "Stale Role"},
    "v5_processed_job_data": {"company_name": "OldCo"},
}


def build_page_html(
    hits: list[dict[str, Any]],
    *,
    page: int = 0,
    total: int = 551,
    is_last: bool = False,
) -> str:
    payload = {
        "props": {
            "pageProps": {
                "ssrHits": hits,
                "ssrPage": page,
                "ssrTotalCount": total,
                "ssrPageSize": 40,
                "ssrIsLastPage": is_last,
            }
        }
    }
    return (
        "<html><body><div>chrome</div>"
        f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(payload)}</script>'
        "</body></html>"
    )


CHALLENGE_HTML = (
    "<html><head><title>Just a moment...</title></head><body>cf-turnstile</body></html>"
)


class FakeTransport:
    def __init__(
        self,
        pages: list[str] | None = None,
        *,
        raise_error: Exception | None = None,
    ) -> None:
        self._pages = (
            pages
            if pages is not None
            else [
                build_page_html([HIT_REMOTE, HIT_ONSITE, HIT_EXPIRED]),
                build_page_html([], is_last=True),
            ]
        )
        self._raise_error = raise_error
        self.calls: list[dict[str, Any]] = []

    def fetch_search_page(self, *, search_state: dict[str, Any], page: int) -> str:
        if self._raise_error is not None:
            raise self._raise_error
        self.calls.append({"search_state": search_state, "page": page})
        index = len(self.calls) - 1
        if index < len(self._pages):
            return self._pages[index]
        return build_page_html([], is_last=True)


@pytest.fixture
def hit_remote() -> dict[str, Any]:
    return HIT_REMOTE


@pytest.fixture
def hit_onsite() -> dict[str, Any]:
    return HIT_ONSITE


@pytest.fixture
def page_builder():
    return build_page_html


@pytest.fixture
def challenge_html() -> str:
    return CHALLENGE_HTML


@pytest.fixture
def fake_transport_cls() -> type[FakeTransport]:
    return FakeTransport
