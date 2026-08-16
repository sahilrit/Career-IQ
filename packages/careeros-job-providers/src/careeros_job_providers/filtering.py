"""Filtering helpers shared by every job provider and the registry."""

from __future__ import annotations

import re

from careeros_job_providers.models import JobPosting, JobSearchQuery


def _keyword_in_text(keyword: str, text: str) -> bool:
    """Whole-word keyword match: "cro" must not match "across"."""
    return re.search(rf"\b{re.escape(keyword.lower())}\b", text) is not None


def matches_query(posting: JobPosting, query: JobSearchQuery) -> bool:
    if query.remote_only and not posting.remote:
        return False

    if query.min_salary is not None:
        midpoint = posting.salary.midpoint() if posting.salary else None
        if midpoint is None or midpoint < query.min_salary:
            return False

    if query.employment_types and posting.employment_type not in query.employment_types:
        return False

    if query.keywords:
        haystack = f"{posting.title} {posting.description} {' '.join(posting.tags)}".lower()
        if not any(_keyword_in_text(keyword, haystack) for keyword in query.keywords):
            return False

    if query.locations:
        if posting.location is None:
            return False
        location_lower = posting.location.lower()
        if not any(loc.lower() in location_lower for loc in query.locations):
            return False

    return True


def filter_postings(postings: list[JobPosting], query: JobSearchQuery) -> list[JobPosting]:
    return [posting for posting in postings if matches_query(posting, query)]
