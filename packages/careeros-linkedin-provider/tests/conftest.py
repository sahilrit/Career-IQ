"""Shared fixtures for LinkedIn provider tests. No real network calls.

The HTML below is a trimmed but structurally faithful copy of a real
response from LinkedIn's guest search endpoint, captured 2026-08-24 —
same class names, same nesting, same whitespace habits (LinkedIn pads
every text node with newlines, which the parser has to strip).
"""

from __future__ import annotations

import pytest

# Two complete cards plus one deliberately broken card with no link, which
# the parser must skip rather than crash on.
SEARCH_HTML = """
<!DOCTYPE html>
<li>
  <div class="base-card relative w-full base-card--link base-search-card job-search-card"
       data-entity-urn="urn:li:jobPosting:4438071583">
    <a class="base-card__full-link" href="https://in.linkedin.com/jobs/view/senior-manager-performance-marketing-at-lenskart-com-4438071583?position=1&amp;pageNum=0&amp;refId=abc">
      <span class="sr-only">
        Senior Manager, Performance Marketing
      </span>
    </a>
    <div class="base-search-card__info">
      <h3 class="base-search-card__title">
        Senior Manager, Performance Marketing
      </h3>
      <h4 class="base-search-card__subtitle">
        <a class="hidden-nested-link" href="https://in.linkedin.com/company/lenskart-com">
          Lenskart.com
        </a>
      </h4>
      <div class="base-search-card__metadata">
        <span class="job-search-card__location">
          New Delhi, Delhi, India
        </span>
        <time class="job-search-card__listdate" datetime="2026-08-04">
          2 weeks ago
        </time>
      </div>
    </div>
  </div>
</li>
<li>
  <div class="base-card base-search-card job-search-card"
       data-entity-urn="urn:li:jobPosting:4400000001">
    <a class="base-card__full-link" href="https://www.linkedin.com/jobs/view/remote-growth-lead-at-widgetco-4400000001">
      <span class="sr-only">Remote Growth Lead</span>
    </a>
    <div class="base-search-card__info">
      <h3 class="base-search-card__title">
        Remote Growth Lead
      </h3>
      <h4 class="base-search-card__subtitle">
        <a class="hidden-nested-link" href="https://www.linkedin.com/company/widgetco">
          WidgetCo
        </a>
      </h4>
      <div class="base-search-card__metadata">
        <span class="job-search-card__location">
          Remote
        </span>
        <span class="job-search-card__salary-info">
          $120,000 - $150,000
        </span>
        <time class="job-search-card__listdate--new" datetime="2026-08-22">
          1 day ago
        </time>
      </div>
    </div>
  </div>
</li>
<li>
  <div class="base-card base-search-card job-search-card">
    <div class="base-search-card__info">
      <h3 class="base-search-card__title">Broken card with no link</h3>
    </div>
  </div>
</li>
"""

JOB_VIEW_HTML = """
<!DOCTYPE html>
<html><body>
  <section class="description">
    <div class="show-more-less-html__markup show-more-less-html__markup--clamp-after-5
                relative overflow-hidden">
      <p>We are looking for a <strong>Senior Manager, Performance Marketing</strong>.</p>
      <p>You will own Google&nbsp;Ads and Meta spend.</p>
      <ul><li>5+ years in paid acquisition</li><li>SQL &amp; dashboards</li></ul>
    </div>
  </section>
</body></html>
"""

EMPTY_HTML = "\n\n"

# A single-card page, used to prove the same job found under two different
# keywords is only returned once.
SEARCH_HTML_ONE_CARD = """
<li>
  <div class="base-card base-search-card job-search-card"
       data-entity-urn="urn:li:jobPosting:4400000001">
    <a class="base-card__full-link" href="https://www.linkedin.com/jobs/view/remote-growth-lead-at-widgetco-4400000001">
      <span class="sr-only">Remote Growth Lead</span>
    </a>
    <div class="base-search-card__info">
      <h3 class="base-search-card__title">Remote Growth Lead</h3>
      <h4 class="base-search-card__subtitle">
        <a class="hidden-nested-link" href="https://www.linkedin.com/company/widgetco">WidgetCo</a>
      </h4>
      <div class="base-search-card__metadata">
        <span class="job-search-card__location">Remote</span>
      </div>
    </div>
  </div>
</li>
"""


class FakeTransport:
    """Records what it was asked for and replays canned HTML."""

    def __init__(
        self,
        pages: list[str] | None = None,
        *,
        job_view_html: str = JOB_VIEW_HTML,
        raise_error: Exception | None = None,
    ) -> None:
        self._pages = pages if pages is not None else [SEARCH_HTML, EMPTY_HTML]
        self._job_view_html = job_view_html
        self._raise_error = raise_error
        self.search_calls: list[dict[str, object]] = []
        self.description_calls: list[str] = []

    def fetch_search_page(self, *, keywords: str, location: str | None, start: int) -> str:
        if self._raise_error is not None:
            raise self._raise_error
        self.search_calls.append({"keywords": keywords, "location": location, "start": start})
        index = len(self.search_calls) - 1
        return self._pages[index] if index < len(self._pages) else EMPTY_HTML

    def fetch_job_page(self, job_id: str) -> str:
        self.description_calls.append(job_id)
        return self._job_view_html


@pytest.fixture
def search_html() -> str:
    return SEARCH_HTML


@pytest.fixture
def job_view_html() -> str:
    return JOB_VIEW_HTML


@pytest.fixture
def one_card_html() -> str:
    return SEARCH_HTML_ONE_CARD


@pytest.fixture
def fake_transport_cls() -> type[FakeTransport]:
    return FakeTransport
