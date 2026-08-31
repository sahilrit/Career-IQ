"""The ATS adapter contract.

An adapter knows exactly three things about its ATS: which hosts it may talk
to, how to turn a company board entry into API URLs, and how to turn one raw
posting into a ``JobPosting``. Everything else — concurrency, error isolation,
health, filtering, dedupe — is the provider's job and is written once.

That split is deliberate: adding an ATS should be one small file, not a new
package with its own crawl loop. Nine adapters ship today and each is under a
hundred lines.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from careeros_ats_providers.http import AtsHttp, assert_allowed
from careeros_job_providers import JobPosting


class BoardEntry:
    """One company's board on one ATS.

    ``slug`` is the ATS's own identifier for the company (Greenhouse board
    token, Lever account, Workday tenant). ``name`` is what a human calls the
    company — used for display and as the posting's company_name when the API
    does not carry one.
    """

    __slots__ = ("extra", "name", "slug")

    def __init__(self, slug: str, name: str | None = None, **extra: Any) -> None:
        self.slug = slug
        self.name = name or slug.replace("-", " ").replace("_", " ").title()
        self.extra = extra

    def __repr__(self) -> str:
        return f"BoardEntry({self.slug!r}, {self.name!r})"


class AtsAdapter(ABC):
    """One hosted ATS."""

    #: Stable id — becomes the posting's source_provider.
    ats_id: str = ""
    #: Hosts this adapter may fetch. An entry starting with "." matches any
    #: subdomain, for the per-tenant ATSes (Workday, BambooHR).
    allowed_hosts: frozenset[str] = frozenset()

    def check(self, url: str) -> str:
        return assert_allowed(url, self.allowed_hosts, ats=self.ats_id)

    @abstractmethod
    def fetch_board(self, entry: BoardEntry, http: AtsHttp) -> list[dict[str, Any]]:
        """Raw postings for one company. Raises BoardFetchError on failure."""

    def probe_board(self, entry: BoardEntry, http: AtsHttp) -> list[dict[str, Any]]:
        """A deliberately CHEAP read of one board, for health checks only.

        Defaults to a full fetch, which is fine for small boards. Adapters
        whose normal fetch is expensive override this: Greenhouse's probe board
        (Stripe, ~570 roles) returns several megabytes with ``content=true``
        and blew the registry's 15s health budget, which silently dropped the
        single largest ATS out of every search. A probe only has to prove the
        board answers with postings, so it must never pay for their bodies.
        """
        return self.fetch_board(entry, http)

    @abstractmethod
    def to_posting(self, raw: dict[str, Any], entry: BoardEntry) -> JobPosting | None:
        """One raw posting as a JobPosting, or None to skip it.

        Returning None is how an adapter drops a record that cannot be applied
        to — most often one with no URL. A posting CareerOS cannot open is
        worse than no posting, because it looks actionable in the UI.
        """

    def probe_entry(self) -> BoardEntry | None:
        """A known-live board used to health-check this ATS. None disables the
        probe (the provider then reports healthy and lets a real search
        surface any problem, rather than paying for a crawl to find out)."""
        return None
