"""Shared fixtures for Naukri provider tests. No real network or browser.

Row shapes mirror the real ``jobapi/v3/search`` response's ``jobDetails[]``
array — field names verified against a live, working scraper's source
(the endpoint itself was confirmed reachable-but-recaptcha-gated in a
live check on 2026-08-24, which is exactly the shape this provider exists
to get past with a real browser).
"""

from __future__ import annotations

from typing import Any

import pytest

ROW_FULL: dict[str, Any] = {
    "jobId": "250824012345",
    "jdURL": "/job-listings-senior-marketing-manager-acme-bengaluru-3-to-6-years-240824012345",
    "companyApplyUrl": "https://acme.example/careers/apply/12345",
    "title": "Senior Marketing Manager",
    "companyName": "Acme Corp",
    "staticUrl": "/acme-corp-jobs-careers-12345",
    "placeholders": [
        {"type": "location", "label": "Bengaluru"},
        {"type": "experience", "label": "3-6 Yrs"},
    ],
    "salaryDetail": {
        "minimumSalary": 1200000,
        "maximumSalary": 1800000,
        "currency": "INR",
        "hideSalary": False,
    },
    "createdDate": 1787217300000,  # 2026-08-20T09:15:00Z in epoch ms
    "jobDescription": "Own the paid-acquisition function across search and social.",
    "tagsAndSkills": "Google Ads, Meta Ads, SQL",
    "experienceText": "3-6 Yrs",
    "logoPathV3": "https://img.naukri.com/logos/acme.png",
    "ambitionBoxData": {"AggregateRating": 4.2, "ReviewsCount": 318},
}

ROW_MINIMAL: dict[str, Any] = {
    "jobId": "250824099999",
    "jdURL": "https://www.naukri.com/job-listings-growth-lead-widgetco-240824099999",
    "title": "Growth Lead",
    "companyName": "WidgetCo",
    "placeholders": [{"type": "location", "label": "Remote"}],
    "salaryDetail": {"hideSalary": True},
    "createdDate": 1787217300000,
}

ROW_UNUSABLE: dict[str, Any] = {"jobId": "1", "title": "No jdURL at all"}

SEARCH_RESPONSE_BODY = (
    '{"jobDetails": ['
    '{"jobId": "1", "jdURL": "/job-1", "title": "A", "companyName": "X"},'
    '{"jobId": "2", "jdURL": "/job-2", "title": "B", "companyName": "Y"}'
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
