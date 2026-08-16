"""careeros_weworkremotely_provider: FIND_JOBS from We Work Remotely's
free public category RSS feeds. Discovery-only (postings link to WWR
listing pages), but strong remote sales/marketing volume.
"""

from __future__ import annotations

import html
import re
from typing import Any, Protocol
from xml.etree import ElementTree

import httpx

from careeros_job_providers import (
    EmploymentType,
    HealthStatus,
    JobPosting,
    JobProvider,
    JobProviderError,
    JobSearchQuery,
    JobSearchResult,
    ProviderHealth,
    filter_postings,
)

USER_AGENT = "CareerOS/0.1 (+https://github.com/careeros; job-discovery bot)"
PROVIDER_ID = "weworkremotely"
_TAG_RE = re.compile(r"<[^>]+>")

# Category RSS feeds most relevant to a marketing/DTC job seeker; add more
# category slugs to widen coverage.
DEFAULT_FEEDS: tuple[str, ...] = (
    "remote-sales-and-marketing-jobs",
    "remote-customer-support-jobs",
    "remote-management-and-finance-jobs",
    "remote-product-jobs",
)
_FEED_URL = "https://weworkremotely.com/categories/{slug}.rss"


class WeWorkRemotelyTransport(Protocol):
    def fetch(self) -> list[dict[str, Any]]: ...


class HttpxWeWorkRemotelyTransport:
    def __init__(
        self,
        *,
        feeds: tuple[str, ...] = DEFAULT_FEEDS,
        timeout: float = 15.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._feeds = feeds
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout)

    def fetch(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        any_ok = False
        for slug in self._feeds:
            try:
                response = self._client.get(
                    _FEED_URL.format(slug=slug), headers={"User-Agent": USER_AGENT}
                )
                response.raise_for_status()
                root = ElementTree.fromstring(response.text)
            except (httpx.HTTPError, ElementTree.ParseError):
                continue
            any_ok = True
            for item in root.iter("item"):
                items.append({child.tag: (child.text or "") for child in item})
        if not any_ok and self._feeds:
            raise JobProviderError("Every We Work Remotely feed request failed")
        return items

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


def parse_job_entry(entry: dict[str, Any]) -> JobPosting:
    raw_title = html.unescape(entry.get("title") or "")
    # WWR titles are "Company: Role"; split on the first colon.
    company, _, role = raw_title.partition(":")
    if not role:
        company, role = "", raw_title
    description = html.unescape(_TAG_RE.sub(" ", entry.get("description") or "")).strip()
    region = entry.get("region") or ""
    return JobPosting(
        source_provider=PROVIDER_ID,
        external_id=entry.get("link") or raw_title,
        title=role.strip(),
        company_name=company.strip(),
        url=(entry.get("link") or "").strip(),
        location=region or None,
        remote=True,
        salary=None,
        employment_type=EmploymentType.FULL_TIME,
        description=description,
        tags=[t.strip().lower() for t in (entry.get("category") or "").split(",") if t.strip()],
        posted_at=None,
    )


class WeWorkRemotelyProvider(JobProvider):
    def __init__(self, transport: WeWorkRemotelyTransport | None = None) -> None:
        self._transport = transport or HttpxWeWorkRemotelyTransport()

    @property
    def provider_id(self) -> str:
        return PROVIDER_ID

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        postings = [parse_job_entry(entry) for entry in self._transport.fetch()]
        return JobSearchResult(postings=filter_postings(postings, query)[: query.limit])

    def health_check(self) -> ProviderHealth:
        try:
            self._transport.fetch()
        except Exception as exc:
            return ProviderHealth(status=HealthStatus.DOWN, detail=str(exc))
        return ProviderHealth(status=HealthStatus.HEALTHY)


__all__ = [
    "DEFAULT_FEEDS",
    "HttpxWeWorkRemotelyTransport",
    "WeWorkRemotelyProvider",
    "WeWorkRemotelyTransport",
    "parse_job_entry",
]
