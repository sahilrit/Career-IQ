"""UkVisaJobsProvider: FIND_JOBS over UK Visa Jobs via a credentialed login.

Local-daemon-only: needs a real browser for login and, more importantly,
the user's own my.ukvisajobs.com email/password. Not part of
``default_provider_registry`` (see ``docs/plans/browser-gated-sources.md``)
— register it explicitly wherever a real browser and the user's own
credentials are actually available, with those credentials resolved from
the workspace's credential vault (never hardcoded, never logged).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager

from careeros_browser import BrowserSession, SelectorTimeoutError, launch_camoufox_session
from careeros_common import get_logger
from careeros_job_providers import (
    HealthStatus,
    JobPosting,
    JobProvider,
    JobSearchQuery,
    JobSearchResult,
    ProviderHealth,
)
from careeros_ukvisajobs_provider.client import (
    AuthSession,
    HttpxUkVisaJobsTransport,
    UkVisaJobsTransport,
)
from careeros_ukvisajobs_provider.parser import (
    JOBS_PER_PAGE,
    OPEN_JOBS_URL,
    PROVIDER_ID,
    SIGNIN_URL,
    is_auth_error,
    is_job_entry,
    parse_job_entry,
    parse_search_response,
)

logger = get_logger(__name__)

DEFAULT_TERM = None
DEFAULT_MAX_PAGES = 4
LOGIN_TIMEOUT_MS = 20_000

SessionFactory = Callable[[], AbstractContextManager[BrowserSession]]


@contextmanager
def _default_session_factory() -> Iterator[BrowserSession]:
    with launch_camoufox_session() as session:
        yield session


class UkVisaJobsProvider(JobProvider):
    def __init__(
        self,
        *,
        session_factory: SessionFactory | None = None,
        transport: UkVisaJobsTransport | None = None,
        credentials: tuple[str, str] | None,
        max_pages: int = DEFAULT_MAX_PAGES,
    ) -> None:
        self._session_factory = session_factory or _default_session_factory
        self._transport = transport or HttpxUkVisaJobsTransport()
        self._credentials = credentials
        self._max_pages = max(1, max_pages)

    @property
    def provider_id(self) -> str:
        return PROVIDER_ID

    def _login(self, session: BrowserSession, *, email: str, password: str) -> AuthSession | None:
        session.goto(SIGNIN_URL)
        try:
            session.wait_for_selector("#email", timeout_ms=LOGIN_TIMEOUT_MS)
        except SelectorTimeoutError:
            return None

        session.fill("#email", email)
        session.fill("#password", password)
        session.press("#password", "Enter")

        # The site sets its session cookies once the post-login redirect
        # lands; navigating to the jobs page itself confirms the session is
        # actually usable, not just that the form was submitted.
        session.goto(OPEN_JOBS_URL)

        cookies = {c.get("name"): c.get("value") for c in session.get_cookies()}
        auth_token = cookies.get("authToken")
        if not auth_token:
            return None

        return AuthSession(
            token=auth_token,
            csrf_token=cookies.get("csrf_token") or "",
            ci_session=cookies.get("ci_session") or "",
            user_agent=session.user_agent(),
        )

    def _search_one_term(
        self,
        auth: AuthSession,
        *,
        search_keyword: str | None,
        limit: int,
        source_errors: list[str],
    ) -> list[JobPosting]:
        postings: list[JobPosting] = []
        page_no = 1

        while page_no <= self._max_pages and len(postings) < limit:
            status_code, body = self._transport.fetch_page(
                page_no=page_no, search_keyword=search_keyword, session=auth
            )

            if is_auth_error(status_code, body):
                source_errors.append(
                    f"ukvisajobs: session expired on page {page_no} "
                    f"(term {search_keyword!r}, HTTP {status_code})"
                )
                break

            parsed = parse_search_response(body)
            rows = parsed["jobs"]
            postings.extend(parse_job_entry(row) for row in rows if is_job_entry(row))

            if len(rows) < JOBS_PER_PAGE:
                break
            page_no += 1

        return postings

    def search(self, query: JobSearchQuery) -> JobSearchResult:
        if self._credentials is None:
            return JobSearchResult(
                source_errors=[
                    "ukvisajobs: no credentials configured — connect your "
                    "my.ukvisajobs.com account to search this source"
                ]
            )
        email, password = self._credentials

        terms: list[str | None] = [k.strip() for k in query.keywords if k.strip()] or [DEFAULT_TERM]

        postings: list[JobPosting] = []
        seen: set[str] = set()
        source_errors: list[str] = []

        with self._session_factory() as session:
            auth = self._login(session, email=email, password=password)
            if auth is None:
                return JobSearchResult(
                    source_errors=["ukvisajobs: login failed — check the stored credentials"]
                )

            for term in terms:
                for posting in self._search_one_term(
                    auth,
                    search_keyword=term,
                    limit=query.limit,
                    source_errors=source_errors,
                ):
                    if posting.external_id in seen:
                        continue
                    seen.add(posting.external_id)
                    postings.append(posting)
                if len(postings) >= query.limit:
                    break

        return JobSearchResult(postings=postings[: query.limit], source_errors=source_errors)

    def health_check(self) -> ProviderHealth:
        # Optimistic, matching NaukriProvider/GradcrackerProvider: a real
        # check would mean logging in on every health probe, which the
        # registry runs before every search — doubling the cost for no
        # benefit, since search() already reports a failed login through
        # source_errors, which is where the real signal belongs.
        return ProviderHealth(status=HealthStatus.HEALTHY)
