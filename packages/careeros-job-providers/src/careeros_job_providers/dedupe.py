"""Deduplication for job postings aggregated across multiple providers.

Two different duplicates exist, and only one of them was being handled.

1. **Within a provider.** The same posting returned twice by one source.
   ``(source_provider, external_id)`` catches these exactly.
2. **Across providers.** The same job reached from an aggregator AND from the
   ATS it is hosted on. These share no ids — Himalayas calls it ``h-8891`` and
   Greenhouse calls it ``4001209002`` — so key (1) never matched them, and the
   user saw the same role twice in one search. That is the duplicate that
   actually shows up in daily use.

The second pass is deliberately conservative, because a wrong merge silently
HIDES a real job, which is worse than showing one twice:

* Identical apply URL is unambiguous and merges with no further conditions.
* Otherwise company + title + location must ALL be present and match. A
  posting missing any of them is never merged on identity, because "" == ""
  would collapse unrelated rows.

When two are merged we keep the more useful one rather than the first one
seen: a posting on the ATS host can actually be applied to, and a posting with
a description can be scored properly.
"""

from __future__ import annotations

import re

from careeros_job_providers.models import JobPosting

_PUNCT_RE = re.compile(r"[^a-z0-9]+")
#: Decorations employers add to a title that do not change which job it is.
_TITLE_NOISE_RE = re.compile(
    r"\b(remote|hybrid|onsite|on site|full time|part time|contract|m f d|m w d|w m d)\b"
)


def _normalize(text: str | None) -> str:
    return _PUNCT_RE.sub(" ", (text or "").lower()).strip()


def normalize_title(title: str | None) -> str:
    """A title with the decorations stripped, so "Growth Marketer (Remote)"
    and "Growth Marketer" are recognised as one job."""
    return _TITLE_NOISE_RE.sub(" ", _normalize(title)).strip()


def normalize_url(url: str | None) -> str:
    """A URL without the scheme, tracking parameters or trailing slash.

    Aggregators append their own ``?utm_source=…`` to the employer's link, so
    the raw strings differ while pointing at exactly the same application.
    """
    raw = (url or "").strip().lower()
    if not raw:
        return ""
    raw = raw.split("#")[0].split("?")[0]
    for prefix in ("https://", "http://"):
        if raw.startswith(prefix):
            raw = raw[len(prefix) :]
    if raw.startswith("www."):
        raw = raw[4:]
    return raw.rstrip("/")


def identity_key(posting: JobPosting) -> tuple[str, str, str] | None:
    """The cross-provider identity of a posting, or None if it cannot be known.

    None is returned whenever any part is missing. Merging on a partial key
    would collapse unrelated postings, and losing a real job to a bad merge is
    worse than showing a duplicate.
    """
    company = _normalize(posting.company_name)
    title = normalize_title(posting.title)
    if posting.location:
        location = _normalize(posting.location)
    else:
        location = "remote" if posting.remote else ""
    if not company or not title or not location:
        return None
    return (company, title, location)


def _is_better(candidate: JobPosting, incumbent: JobPosting) -> bool:
    """Whether ``candidate`` is the more useful copy of the same job.

    An ATS-hosted posting wins because it is the one that can actually be
    applied to; after that, whichever carries a description, since that is what
    scoring reads.
    """
    candidate_ats = (candidate.source_provider or "").startswith("ats:")
    incumbent_ats = (incumbent.source_provider or "").startswith("ats:")
    if candidate_ats != incumbent_ats:
        return candidate_ats
    if bool(candidate.description) != bool(incumbent.description):
        return bool(candidate.description)
    return len(candidate.description or "") > len(incumbent.description or "")


def deduplicate(postings: list[JobPosting], *, cross_provider: bool = True) -> list[JobPosting]:
    """One row per real job.

    ``cross_provider=False`` restricts this to the within-provider key, for
    callers that genuinely want every source's copy.
    """
    seen: set[tuple[str, str]] = set()
    unique: list[JobPosting] = []
    for posting in postings:
        key = posting.dedupe_key
        if key in seen:
            continue
        seen.add(key)
        unique.append(posting)

    if not cross_provider:
        return unique
    return _merge_across_providers(unique)


def _merge_across_providers(postings: list[JobPosting]) -> list[JobPosting]:
    #: index into ``kept`` for each canonical key, so a later, better copy can
    #: REPLACE an earlier one in place and the original ordering survives.
    positions: dict[tuple, int] = {}
    kept: list[JobPosting] = []

    for posting in postings:
        keys: list[tuple] = []
        url = normalize_url(posting.apply_url or posting.url)
        if url:
            keys.append(("url", url))
        identity = identity_key(posting)
        if identity is not None:
            keys.append(("identity", *identity))

        existing_at = next((positions[k] for k in keys if k in positions), None)
        if existing_at is None:
            index = len(kept)
            kept.append(posting)
            for key in keys:
                positions[key] = index
            continue

        if _is_better(posting, kept[existing_at]):
            kept[existing_at] = posting
        # Both copies' keys now point at the surviving row, so a third copy
        # matching EITHER of them merges too.
        for key in keys:
            positions.setdefault(key, existing_at)

    return kept
