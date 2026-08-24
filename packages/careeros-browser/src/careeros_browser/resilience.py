"""Reusable resilience primitives for sources behind bot protection.

These are the pure-Python pieces of an anti-bot strategy — the parts that
need no browser binary and are worth testing on their own:

* **Challenge detection** — recognise a Cloudflare interstitial by page
  content and by HTTP status. The managed challenge returns HTTP 200 with
  challenge HTML, so content detection has to exist alongside the status
  check, not instead of it.
* **A persistent cookie jar keyed to its user-agent.** Cloudflare binds a
  ``cf_clearance`` cookie to the exact UA (and TLS fingerprint) that
  earned it, so the cookie and the UA are stored and reloaded together —
  a clearance cookie replayed under a different UA is worthless.
* **Retry with backoff** — for the transient failures these sources throw.

The heavier machinery an actively-blocked source also needs — an
anti-detect browser build (Camoufox), a headed human-solve flow, TLS
fingerprint spoofing — is deployment-level and only earns its keep once a
provider that hits a hard block is added. It is deliberately not built
here: none of the current providers reach a site that gates them, so that
infrastructure would be untested and unused. When such a provider lands,
these primitives are the reusable core it builds on.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from pydantic import BaseModel, Field

from careeros_common import DocumentStore

# Content markers of a Cloudflare challenge, gathered empirically. These will
# need updating if Cloudflare changes their challenge page structure.
CF_CHALLENGE_MARKERS: tuple[str, ...] = (
    "cf-challenge-running",
    "cf-turnstile",
    "checking your browser",
    "challenges.cloudflare.com",
    "just a moment...",
    "cf-please-wait",
    "cf_chl_opt",
    "cf-browser-verification",
)

#: Cookies worth persisting: the CF clearance proof plus common session names.
_PERSIST_HINTS = ("cf_clearance", "__cf_bm", "cf_chl_2", "cf_chl_prog", "__cflb")

_CLEARANCE_COOKIE = "cf_clearance"
_ENTITY = "browser_cookie_jar"


def is_challenge_html(html: str) -> bool:
    """Whether page content looks like a Cloudflare challenge."""
    lowered = html.lower()
    return any(marker in lowered for marker in CF_CHALLENGE_MARKERS)


def is_challenge_status(status_code: int, headers: dict[str, str]) -> bool:
    """Whether an HTTP response looks like a Cloudflare block by status.

    A managed challenge comes back 200, so this only catches the hard 403/503
    blocks; pair it with :func:`is_challenge_html` for the 200 case.
    """
    if status_code not in (403, 503):
        return False
    server = ""
    for key, value in headers.items():
        if key.lower() == "server":
            server = str(value).lower()
            break
    return "cloudflare" in server


class CookieJar(BaseModel):
    """Cookies plus the user-agent that earned them."""

    cookies: dict[str, str] = Field(default_factory=dict)
    user_agent: str = ""

    @property
    def has_clearance(self) -> bool:
        return _CLEARANCE_COOKIE in self.cookies

    def cookie_header(self) -> str:
        """A ``Cookie:`` header value for a plain HTTP client, so a headed
        solve and a fast HTTP retry share one Cloudflare session."""
        return "; ".join(f"{name}={value}" for name, value in self.cookies.items())

    @classmethod
    def from_all(cls, cookies: dict[str, str], user_agent: str) -> CookieJar:
        """Build a jar keeping only the cookies worth persisting."""
        kept = {
            name: value
            for name, value in cookies.items()
            if name in _PERSIST_HINTS or "session" in name.lower() or "auth" in name.lower()
        }
        return cls(cookies=kept, user_agent=user_agent)


class PersistentCookieStore:
    """Saves and loads a :class:`CookieJar` per extractor id.

    Store-backed so it fits the tenancy model — a workspace's clearance
    cookies never leak across the boundary — rather than a shared file.
    """

    def __init__(self, store: DocumentStore) -> None:
        self._store = store

    def save(self, extractor_id: str, jar: CookieJar) -> None:
        self._store.put(_ENTITY, extractor_id, jar.model_dump(mode="json"))

    def load(self, extractor_id: str) -> CookieJar | None:
        raw = self._store.get_or_none(_ENTITY, extractor_id)
        return CookieJar.model_validate(raw) if raw else None

    def invalidate(self, extractor_id: str) -> None:
        self._store.delete(_ENTITY, extractor_id)


def retry_with_backoff[T](
    fn: Callable[[], T],
    *,
    max_attempts: int = 3,
    base_delay: float = 2.0,
    should_retry: Callable[[Exception], bool] | None = None,
) -> T:
    """Call ``fn``, retrying on failure with exponential backoff.

    ``should_retry`` can classify an exception as terminal (return False) so a
    permanent error — a 401, a parse failure — is not pointlessly retried.
    The final failure is re-raised.
    """
    if max_attempts < 1:
        raise ValueError(f"max_attempts must be >= 1, got {max_attempts}")

    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as exc:
            last_error = exc
            if should_retry is not None and not should_retry(exc):
                raise
            if attempt < max_attempts:
                time.sleep(base_delay * 2 ** (attempt - 1))

    assert last_error is not None
    raise last_error
