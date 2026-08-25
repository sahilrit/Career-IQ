"""HTTP transport for UK Visa Jobs' paginated search API.

The login itself needs a real browser (client-rendered SPA, possibly behind
a Cloudflare challenge — see ``provider.py``), but once authenticated the
search API is a plain multipart POST. Reusing a browser instance for every
page would be far more expensive than necessary, so this makes the request
directly with the cookies/token/UA the login step captured.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx

from careeros_ukvisajobs_provider.parser import API_URL, OPEN_JOBS_URL, build_search_form_fields


@dataclass(frozen=True)
class AuthSession:
    token: str
    csrf_token: str
    ci_session: str
    user_agent: str


class UkVisaJobsTransport(Protocol):
    def fetch_page(
        self, *, page_no: int, search_keyword: str | None, session: AuthSession
    ) -> tuple[int, str]:
        """Fetch one page, returning ``(status_code, response_body)``.

        Returns the status code rather than raising on a non-2xx response —
        an auth-expired 401/403/400 is an ordinary, expected outcome the
        caller needs to distinguish from a genuinely empty page, not an
        exceptional one.
        """
        ...


def _cookie_header(session: AuthSession) -> str:
    parts = []
    if session.csrf_token:
        parts.append(f"csrf_token={session.csrf_token}")
    if session.ci_session:
        parts.append(f"ci_session={session.ci_session}")
    if session.token:
        parts.append(f"authToken={session.token}")
    return "; ".join(parts)


class HttpxUkVisaJobsTransport:
    def __init__(self, *, timeout: float = 15.0, client: httpx.Client | None = None) -> None:
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=timeout)

    def fetch_page(
        self, *, page_no: int, search_keyword: str | None, session: AuthSession
    ) -> tuple[int, str]:
        fields = build_search_form_fields(
            page_no=page_no, search_keyword=search_keyword, token=session.token
        )
        headers = {
            "accept": "application/json, text/plain, */*",
            "cookie": _cookie_header(session),
            "origin": "https://my.ukvisajobs.com",
            "referer": OPEN_JOBS_URL,
            "user-agent": session.user_agent,
        }
        response = self._client.post(API_URL, data=fields, headers=headers)
        return response.status_code, response.text

    def close(self) -> None:
        if self._owns_client:
            self._client.close()
