"""Deduplication for gig postings aggregated across multiple providers."""

from __future__ import annotations

from careeros_freelance_providers.models import GigPosting


def deduplicate(postings: list[GigPosting]) -> list[GigPosting]:
    """Drop postings sharing a ``(source_provider, external_id)`` key, keeping the first."""
    seen: set[tuple[str, str]] = set()
    unique: list[GigPosting] = []
    for posting in postings:
        key = posting.dedupe_key
        if key in seen:
            continue
        seen.add(key)
        unique.append(posting)
    return unique
