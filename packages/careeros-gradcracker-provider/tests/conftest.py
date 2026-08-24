"""Shared fixtures for Gradcracker provider tests. No real network or
browser.

The article markup below is a reconstruction, not a capture. Gradcracker
is Cloudflare-protected — every direct fetch from this environment
returned HTTP 403 (verified 2026-08-24) — so unlike Naukri's JSON API
there was no way to inspect real production HTML here. What grounds this
fixture instead is a set of *verified* Playwright locator queries from a
working scraper's source: ``article[wire\\:key]`` per card, ``h2 a`` for
the title/link, ``figure img@alt`` for the employer, ``figure a@href``
for the employer link, an ``h3`` for disciplines, a div containing
"Deadline:", and ``dt``/``dd`` pairs for Salary/Location/Degree
required/Starting. The fixture below is the simplest markup consistent
with every one of those locators actually working — if Gradcracker's
real DOM differs in some other respect, the shape captured by these
specific locators is exactly the shape this parser depends on.
"""

from __future__ import annotations

import pytest

ARTICLE_FULL = """
<article wire:key="job-441122">
  <figure>
    <a href="/employers/acme-engineering">
      <img src="/logos/acme.png" alt="Acme Engineering">
    </a>
  </figure>
  <h2><a href="/jobs/software-engineering-graduate-scheme-acme-441122">
    Software Engineering Graduate Scheme
  </a></h2>
  <h3>Software Engineering, Web Development</h3>
  <div class="pill">Deadline: 30th September 2026</div>
  <dl>
    <dt>Salary</dt><dd>£28,000 - £32,000</dd>
    <dt>Location</dt><dd>Leeds, Yorkshire</dd>
    <dt>Degree required</dt><dd>2:1</dd>
    <dt>Starting</dt><dd>September 2026</dd>
  </dl>
</article>
"""

ARTICLE_MINIMAL = """
<article wire:key="job-559900">
  <h2><a href="/jobs/remote-graduate-developer-widgetco-559900">Remote Graduate Developer</a></h2>
  <dl>
    <dt>Location</dt><dd>Remote (UK-wide)</dd>
  </dl>
</article>
"""

ARTICLE_COMPETITIVE_SALARY = """
<article wire:key="job-771122">
  <h2><a href="/jobs/graduate-analyst-gamma-771122">Graduate Analyst</a></h2>
  <dl>
    <dt>Salary</dt><dd>Competitive</dd>
    <dt>Location</dt><dd>Manchester</dd>
  </dl>
</article>
"""

ARTICLE_NO_LINK = """
<article wire:key="job-broken">
  <h2>No link here</h2>
</article>
"""

LIST_PAGE_HTML = f"{ARTICLE_FULL}\n{ARTICLE_MINIMAL}"


@pytest.fixture
def article_full() -> str:
    return ARTICLE_FULL


@pytest.fixture
def article_minimal() -> str:
    return ARTICLE_MINIMAL


@pytest.fixture
def article_competitive_salary() -> str:
    return ARTICLE_COMPETITIVE_SALARY


@pytest.fixture
def article_no_link() -> str:
    return ARTICLE_NO_LINK


@pytest.fixture
def list_page_articles() -> list[str]:
    return [ARTICLE_FULL, ARTICLE_MINIMAL]
