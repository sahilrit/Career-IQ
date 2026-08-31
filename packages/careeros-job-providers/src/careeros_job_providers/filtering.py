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


def keyword_matches_posting(keyword: str, posting: JobPosting) -> bool:
    """Whether ``keyword`` is a real signal for this posting.

    The title (plus tags) is the primary signal. Matching a keyword anywhere in
    a full job description is far too loose to be useful: measured against
    2,170 live Lever postings, "any hit in title or description" for a set of
    marketing keywords kept 987 of them — including "Liquor Store Associate",
    which mentions "performance" once in a boilerplate paragraph. Title-only
    matching kept 79, essentially all genuinely relevant.

    A description hit is therefore only trusted for MULTI-WORD keywords. A
    phrase like "performance marketing" or "demand generation" appearing in a
    body really is about the role; a bare "marketing" is not. That single
    distinction recovers the handful of real matches whose title is vague
    ("Senior Manager, Digital") without readmitting the noise.
    """
    lowered = keyword.strip().lower()
    if not lowered:
        return False
    headline = f"{posting.title} {' '.join(posting.tags)}".lower()
    if _keyword_in_text(lowered, headline):
        return True
    if " " in lowered and posting.description:
        return _keyword_in_text(lowered, posting.description.lower())
    return False


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

    if (
        query.keywords
        and "keywords" not in applied
        and not any(keyword_matches_posting(keyword, posting) for keyword in query.keywords)
    ):
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
