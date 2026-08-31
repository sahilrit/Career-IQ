"""Shared HTTP for ATS board fetches.

Every ATS adapter derives an API URL from a company slug or a careers URL,
which means a hostile or mistyped board entry could otherwise point the
fetcher anywhere. Each adapter therefore declares the exact hosts it is
allowed to talk to, and this module enforces that on the final URL — the one
that actually goes over the wire, after query parameters are added.

Redirects are disabled rather than followed: a followed redirect can leave the
allowlist, which is the classic SSRF hole in "just fetch the board" code. This
guard is adapted from the same pattern used by career-ops (MIT).
"""

from __future__ import annotations

from urllib.parse import urlparse

import httpx

from careeros_common import get_logger

logger = get_logger(__name__)

USER_AGENT = "CareerOS/0.1 (+https://github.com/careeros; job-discovery bot)"
DEFAULT_TIMEOUT = 20.0


class BoardFetchError(Exception):
    """One board could not be read. Never fatal to a whole crawl."""


def assert_allowed(url: str, allowed_hosts: frozenset[str], *, ats: str) -> str:
    """The URL, if it is HTTPS and on an allowed host. Raises otherwise."""
    try:
        parsed = urlparse(url)
    except ValueError as exc:
        raise BoardFetchError(f"{ats}: invalid URL {url!r}") from exc
    if parsed.scheme != "https":
        raise BoardFetchError(f"{ats}: URL must use HTTPS: {url}")
    host = (parsed.hostname or "").lower()
    # A suffix entry (".myworkdayjobs.com") covers per-tenant subdomains, which
    # Workday and BambooHR both use; an exact entry covers everything else.
    ok = any(host == h or (h.startswith(".") and host.endswith(h)) for h in allowed_hosts)
    if not ok:
        raise BoardFetchError(
            f"{ats}: untrusted host {host!r} — allowed: {', '.join(sorted(allowed_hosts))}"
        )
    return url


class AtsHttp:
    """A small JSON/text fetcher shared by every adapter."""

    def __init__(self, client: httpx.Client | None = None, *, timeout: float = DEFAULT_TIMEOUT):
        self._owns = client is None
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=False)

    def _request(self, url: str, *, method: str = "GET", json_body=None, headers=None):
        merged = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        if headers:
            merged.update(headers)
        try:
            response = self._client.request(method, url, json=json_body, headers=merged)
        except httpx.HTTPError as exc:
            raise BoardFetchError(f"request to {url} failed: {exc}") from exc
        if response.is_redirect:
            raise BoardFetchError(
                f"{url} redirected to {response.headers.get('location', '?')} — "
                "not followed, because a redirect can leave the host allowlist"
            )
        if response.status_code >= 400:
            raise BoardFetchError(f"{url} returned {response.status_code}")
        return response

    def get_json(self, url: str, *, headers=None):
        response = self._request(url, headers=headers)
        try:
            return response.json()
        except ValueError as exc:
            raise BoardFetchError(f"{url} did not return JSON") from exc

    def post_json(self, url: str, body, *, headers=None):
        response = self._request(url, method="POST", json_body=body, headers=headers)
        try:
            return response.json()
        except ValueError as exc:
            raise BoardFetchError(f"{url} did not return JSON") from exc

    def get_text(self, url: str, *, headers=None) -> str:
        return self._request(url, headers=headers).text

    def close(self) -> None:
        if self._owns:
            self._client.close()
