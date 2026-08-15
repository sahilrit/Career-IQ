"""Deduplication for job postings aggregated across multiple providers."""

from __future__ import annotations

from careeros_job_providers.models import JobPosting


def deduplicate(postings: list[JobPosting]) -> list[JobPosting]:
    """Drop postings sharing a ``(source_provider, external_id)`` key, keeping the first."""
    seen: set[tuple[str, str]] = set()
    unique: list[JobPosting] = []
    for posting in postings:
        key = posting.dedupe_key
        if key in seen:
            continue
        seen.add(key)
        unique.append(posting)
    return unique
