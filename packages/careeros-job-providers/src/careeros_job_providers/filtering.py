"""Filtering helpers shared by every job provider and the registry.

Most of our providers hand back a whole feed and rely on these helpers to
narrow it. A few — LinkedIn, Indeed, Adzuna — take the keywords and the
location into their own query instead, and for those, re-filtering here is
actively harmful: our haystack is only the fields we managed to parse, so
a posting whose description has not been fetched yet gets dropped even
though the source matched it on full text. Those providers pass
``applied_server_side`` to say which filters they already honoured.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from careeros_job_providers.models import JobPosting, JobSearchQuery

#: Filters a provider may declare it has already applied at the source.
SERVER_SIDE_FILTERABLE = frozenset({"keywords", "locations"})


def _keyword_in_text(keyword: str, text: str) -> bool:
    """Whole-word keyword match: "cro" must not match "across"."""
    return re.search(rf"\b{re.escape(keyword.lower())}\b", text) is not None


def _validated(applied_server_side: Iterable[str]) -> frozenset[str]:
    applied = frozenset(applied_server_side)
    unknown = applied - SERVER_SIDE_FILTERABLE
    if unknown:
        raise ValueError(
            f"{', '.join(sorted(unknown))} is not a filterable field; "
            f"expected any of {', '.join(sorted(SERVER_SIDE_FILTERABLE))}"
        )
    return applied


def matches_query(
    posting: JobPosting,
    query: JobSearchQuery,
    *,
    applied_server_side: Iterable[str] = (),
) -> bool:
    applied = _validated(applied_server_side)

    if query.remote_only and not posting.remote:
        return False

    if query.min_salary is not None:
        midpoint = posting.salary.midpoint() if posting.salary else None
        if midpoint is None or midpoint < query.min_salary:
            return False

    if query.employment_types and posting.employment_type not in query.employment_types:
        return False

    if query.keywords and "keywords" not in applied:
        haystack = f"{posting.title} {posting.description} {' '.join(posting.tags)}".lower()
        if not any(_keyword_in_text(keyword, haystack) for keyword in query.keywords):
            return False

    if query.locations and "locations" not in applied:
        if posting.location is None:
            return False
        location_lower = posting.location.lower()
        if not any(loc.lower() in location_lower for loc in query.locations):
            return False

    return True


def filter_postings(
    postings: list[JobPosting],
    query: JobSearchQuery,
    *,
    applied_server_side: Iterable[str] = (),
) -> list[JobPosting]:
    applied = _validated(applied_server_side)
    return [
        posting
        for posting in postings
        if matches_query(posting, query, applied_server_side=applied)
    ]
