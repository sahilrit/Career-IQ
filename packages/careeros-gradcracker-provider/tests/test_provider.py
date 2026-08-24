"""Tests for GradcrackerProvider — entirely offline, via a fake browser
session."""

from __future__ import annotations

from contextlib import contextmanager

from careeros_browser import FakeBrowserSession
from careeros_gradcracker_provider.parser import CARD_SELECTOR
from careeros_gradcracker_provider.provider import GradcrackerProvider
from careeros_job_providers import HealthStatus, JobSearchQuery

ARTICLE_A = """
<article wire:key="a">
  <h2><a href="/jobs/software-engineer-acme-1">Software Engineer</a></h2>
  <figure><img src="x.png" alt="Acme"></figure>
  <dl><dt>Location</dt><dd>Leeds</dd></dl>
</article>
"""
ARTICLE_B = """
<article wire:key="b">
  <h2><a href="/jobs/backend-developer-beta-2">Backend Developer</a></h2>
  <figure><img src="y.png" alt="Beta"></figure>
  <dl><dt>Location</dt><dd>Manchester</dd></dl>
</article>
"""


@contextmanager
def _session_factory(session: FakeBrowserSession):
    try:
        yield session
    finally:
        session.close()


def _provider(session: FakeBrowserSession, **kwargs) -> GradcrackerProvider:
    return GradcrackerProvider(session_factory=lambda: _session_factory(session), **kwargs)


def _seed(session: FakeBrowserSession, articles: list[str]) -> None:
    session.set_visible(CARD_SELECTOR)
    session.set_html_blocks(CARD_SELECTOR, articles)


def test_provider_id_is_gradcracker():
    session = FakeBrowserSession()
    assert _provider(session).provider_id == "gradcracker"


def test_search_returns_postings_from_every_role_region_combo():
    session = FakeBrowserSession()
    _seed(session, [ARTICLE_A, ARTICLE_B])

    result = _provider(session, roles=("web-development",), regions=("yorkshire",)).search(
        JobSearchQuery(limit=50)
    )

    assert {p.title for p in result.postings} == {"Software Engineer", "Backend Developer"}


def test_search_uses_query_keywords_as_roles_when_given():
    session = FakeBrowserSession()
    _seed(session, [ARTICLE_A])

    _provider(session, regions=("yorkshire",)).search(
        JobSearchQuery(keywords=["data-science"], limit=10)
    )

    assert "data-science-graduate-jobs" in session.current_url


def test_search_iterates_multiple_regions():
    session = FakeBrowserSession()
    _seed(session, [ARTICLE_A])

    result = _provider(
        session, roles=("web-development",), regions=("yorkshire", "north-west")
    ).search(JobSearchQuery(limit=50))

    # Same fixture served for both region navigations; both contribute,
    # deduped by URL since it's the same posting each time.
    assert len(result.postings) == 1


def test_search_stops_once_the_limit_is_reached():
    session = FakeBrowserSession()
    _seed(session, [ARTICLE_A, ARTICLE_B])

    result = _provider(session, roles=("web-development",), regions=("yorkshire",)).search(
        JobSearchQuery(limit=1)
    )

    assert len(result.postings) == 1


def test_a_region_with_no_cards_contributes_nothing_and_is_not_an_error():
    session = FakeBrowserSession()
    session.set_visible(CARD_SELECTOR)
    session.set_html_blocks(CARD_SELECTOR, [])  # rendered, but empty

    result = _provider(session, roles=("web-development",), regions=("yorkshire",)).search(
        JobSearchQuery(limit=10)
    )

    assert result.postings == []
    assert result.source_errors == []


def test_a_challenge_that_blocks_every_combo_is_reported():
    """The card selector never becomes visible in any combo — every request
    was intercepted. This must be distinguishable from 'legitimately no
    graduate roles anywhere in the UK right now'."""
    session = FakeBrowserSession()  # nothing ever made visible

    result = _provider(session, roles=("web-development",), regions=("yorkshire",)).search(
        JobSearchQuery(limit=10)
    )

    assert result.postings == []
    assert result.source_errors


def test_one_blocked_combo_among_others_does_not_report_an_error():
    """A single empty/blocked region among several that work is ordinary —
    only a total wipeout is worth surfacing."""

    class SwitchingSession(FakeBrowserSession):
        """Blocks the card selector for the first navigation only."""

        def __init__(self) -> None:
            super().__init__()
            self._navigations = 0

        def goto(self, url: str) -> None:
            super().goto(url)
            self._navigations += 1
            if self._navigations == 1:
                self.set_hidden(CARD_SELECTOR)
                self.set_html_blocks(CARD_SELECTOR, [])
            else:
                self.set_visible(CARD_SELECTOR)
                self.set_html_blocks(CARD_SELECTOR, [ARTICLE_A])

    session = SwitchingSession()
    result = _provider(
        session, roles=("web-development",), regions=("yorkshire", "north-west")
    ).search(JobSearchQuery(limit=10))

    assert len(result.postings) == 1
    assert result.source_errors == []


def test_the_same_posting_across_regions_is_only_returned_once():
    session = FakeBrowserSession()
    _seed(session, [ARTICLE_A])

    result = _provider(
        session, roles=("web-development",), regions=("yorkshire", "north-west", "east-midlands")
    ).search(JobSearchQuery(limit=50))

    assert len(result.postings) == 1


def test_health_check_is_optimistic():
    session = FakeBrowserSession()
    assert _provider(session).health_check().status == HealthStatus.HEALTHY
