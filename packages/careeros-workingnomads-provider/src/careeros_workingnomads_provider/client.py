"""HTTP client for Working Nomads' job search backend.

``/jobsapi/_search`` is the Elasticsearch endpoint the site's own search
UI posts to. It takes a standard query DSL body and returns full documents
— description, salary, tags, publish date — rather than the summary rows
the public feed gives us.
"""

from __future__ import annotations

from typing import Any, Protocol

import httpx

from careeros_job_providers import JobProviderError

WORKINGNOMADS_SEARCH_URL = "https://www.workingnomads.com/jobsapi/_search"
USER_AGENT = "CareerOS/0.1 (+https://github.com/careeros; job-discovery bot)"

#: The index rejects very large page sizes; this is comfortably under it.
MAX_SIZE = 200

#: Elasticsearch scores every document, including near-irrelevant ones. A
#: floor keeps a broad term like "manager" from returning the whole index.
MIN_SCORE = 2

_SEARCH_FIELDS = ["title^2", "description", "company"]


class WorkingNomadsTransport(Protocol):
    def search(self, *, keywords: list[str], size: int) -> list[dict[str, Any]]: ...


def build_search_body(*, keywords: list[str], size: int) -> dict[str, Any]:
    """The query DSL body for a keyword search.

    With no keywords there is nothing to score, so the query is dropped and
    the request becomes "most recent N" — matching what the old feed did.
    """
    body: dict[str, Any] = {"size": max(1, min(size, MAX_SIZE))}
    # Strip embedded double quotes: a term is a phrase to quote, and an inner
    # quote would break the query_string wrapping into malformed syntax that
    # Elasticsearch rejects, silently dropping the term.
    terms = [cleaned for term in keywords if (cleaned := " ".join(term.replace('"', " ").split()))]
    if not terms:
        body["sort"] = [{"pub_date": {"order": "desc"}}]
        return body

    # OR the terms together: a candidate searching "ppc" and "growth" wants
    # postings matching either, the same as every other provider we run.
    body["query"] = {
        "bool": {
            "must": [
                {
                    "query_string": {
                        "query": " OR ".join(f'"{term}"' for term in terms),
                        "fields": _SEARCH_FIELDS,
                    }
                }
            ]
        }
    }
    body["min_score"] = MIN_SCORE
    return body


class HttpxWorkingNomadsTransport:
    def __init__(
        self,
        *,
        base_url: str = WORKINGNOMADS_SEARCH_URL,
        timeout: float = 15.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout)

    def search(self, *, keywords: list[str], size: int) -> list[dict[str, Any]]:
        try:
            response = self._client.post(
                self._base_url,
                json=build_search_body(keywords=keywords, size=size),
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise JobProviderError(f"Working Nomads request failed: {exc}") from exc

        # The endpoint has returned a bare array in the past; tolerate both.
        if isinstance(payload, list):
            return [doc for doc in payload if isinstance(doc, dict)]

        hits = (payload or {}).get("hits", {}).get("hits")
        if not isinstance(hits, list):
            raise JobProviderError("Working Nomads search returned an unexpected payload")
        return [hit["_source"] for hit in hits if isinstance(hit, dict) and "_source" in hit]

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
