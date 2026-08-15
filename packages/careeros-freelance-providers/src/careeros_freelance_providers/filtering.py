"""Filtering helpers shared by every freelance provider and the registry."""

from __future__ import annotations

from careeros_freelance_providers.models import GigPosting, GigSearchQuery


def matches_query(posting: GigPosting, query: GigSearchQuery) -> bool:
    if query.min_budget is not None:
        midpoint = posting.budget.midpoint() if posting.budget else None
        if midpoint is None or midpoint < query.min_budget:
            return False

    if query.project_types and (
        posting.budget is None or posting.budget.project_type not in query.project_types
    ):
        return False

    if query.skills:
        posting_skills_lower = {skill.lower() for skill in posting.skills_required}
        if not any(skill.lower() in posting_skills_lower for skill in query.skills):
            return False

    if query.keywords:
        haystack = f"{posting.title} {posting.description}".lower()
        if not any(keyword.lower() in haystack for keyword in query.keywords):
            return False

    return True


def filter_postings(postings: list[GigPosting], query: GigSearchQuery) -> list[GigPosting]:
    return [posting for posting in postings if matches_query(posting, query)]
