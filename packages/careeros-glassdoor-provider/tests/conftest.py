"""Shared fixtures for Glassdoor provider tests. No real network or browser.

Card HTML mirrors a real Glassdoor search-results job card — captured live
(2026-08-26) after a real Camoufox session passed the site's bot wall.
Every field lives inside one self-contained
``[data-test="job-card-wrapper"]`` element, anchored by stable
``data-test``/``id`` attributes even though the surrounding CSS class
names are build-hashed and will change on Glassdoor's next deploy.
"""

from __future__ import annotations

import pytest

CARD_WITH_SALARY = """
<div class="JobCard_jobCardWrapper__vX29z" data-test="job-card-wrapper" data-selected="true">
  <div class="EmployerProfile_profileContainer__63w3R" id="job-employer-1010229431335">
    <span class="EmployerProfile_compactEmployerName__9MGcV">Dow</span>
  </div>
  <a class="JobCard_jobTitle__GLyJ1" data-test="job-title"
     href="https://www.glassdoor.com/job-listing/senior-marketing-specialist-dow-JV_IC5021997.htm?jl=1010229431335"
     id="job-title-1010229431335" tabindex="-1">Senior Marketing Specialist</a>
  <div class="JobCard_location__Ds1fM" data-test="emp-location"
       id="job-location-1010229431335">Navi Mumbai</div>
  <div class="JobCard_salaryEstimate__QpbTW" data-test="detailSalary"
       id="job-salary-1010229431335">₹5L - ₹8L<!-- -->&nbsp;<span>(Glassdoor Est.)</span></div>
  <div class="JobCard_jobDescriptionSnippet__l1tnl" data-test="descSnippet">
    <div>Experience working on global teams and marketing environments.</div>
  </div>
</div>
"""

CARD_WITHOUT_SALARY = """
<div class="JobCard_jobCardWrapper__vX29z" data-test="job-card-wrapper" data-selected="false">
  <div class="EmployerProfile_profileContainer__63w3R" id="job-employer-1010164065576">
    <span class="EmployerProfile_compactEmployerName__9MGcV">UnitedHealth Group</span>
  </div>
  <a class="JobCard_jobTitle__GLyJ1" data-test="job-title"
     href="https://www.glassdoor.com/job-listing/marketing-manager-uhg-JV_IC2921225.htm?jl=1010164065576"
     id="job-title-1010164065576" tabindex="-1">Marketing Manager</a>
  <div class="JobCard_location__Ds1fM" data-test="emp-location"
       id="job-location-1010164065576">Remote</div>
</div>
"""

CARD_UNUSABLE = '<div data-test="job-card-wrapper">No title link at all</div>'


@pytest.fixture
def card_with_salary() -> str:
    return CARD_WITH_SALARY


@pytest.fixture
def card_without_salary() -> str:
    return CARD_WITHOUT_SALARY


@pytest.fixture
def card_unusable() -> str:
    return CARD_UNUSABLE
