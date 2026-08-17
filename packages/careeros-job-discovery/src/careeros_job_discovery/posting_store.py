"""A small cache of discovered JobPostings, keyed by URL.

Discovery already fetches every posting; storing them means later steps
(application generation, autopilot submission) can read the full posting
back by URL instead of re-crawling every provider to find it again.
"""

from __future__ import annotations

from careeros_common import DocumentStore
from careeros_job_providers import JobPosting

_ENTITY_TYPE = "job_posting"


class JobPostingRepository:
    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, posting: JobPosting) -> None:
        if posting.url:
            self._store.put(_ENTITY_TYPE, posting.url, posting.model_dump(mode="json"))

    def load_or_none(self, url: str) -> JobPosting | None:
        data = self._store.get_or_none(_ENTITY_TYPE, url)
        return JobPosting.model_validate(data) if data is not None else None
