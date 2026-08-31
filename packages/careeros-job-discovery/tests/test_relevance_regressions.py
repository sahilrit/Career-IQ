"""Relevance: the goal is relevant opportunities, not maximum opportunity count.

The measurement behind this file: on 2,170 live Lever postings, matching a set
of marketing keywords "anywhere in title or description" kept 987 — including
"Liquor Store Associate", which mentions "performance" once in a boilerplate
paragraph. Title-anchored matching kept 79, essentially all genuinely relevant.

A filter that tight can fail the other way, so the cases here run in both
directions: obvious matches must survive, obvious mismatches must not, and the
useful edge cases (a vague title with a specific phrase in the body) must still
come through.
"""

from __future__ import annotations

import pytest

from careeros_career_brain import CareerBrain, Identity, Preferences, Skill
from careeros_job_discovery import score_posting
from careeros_job_providers import JobPosting, JobSearchQuery, Salary, filter_postings
from careeros_job_providers.filtering import keyword_matches_posting

MARKETING = [
    "performance marketing",
    "paid media",
    "growth marketing",
    "demand generation",
    "marketing manager",
]


def posting(title: str, **kwargs) -> JobPosting:
    defaults = {
        "source_provider": "test",
        "external_id": title,
        "company_name": "Acme",
        "url": f"https://example.test/{abs(hash(title))}",
        "remote": True,
    }
    return JobPosting(title=title, **{**defaults, **kwargs})


def kept(postings, **query_kwargs) -> list[str]:
    query = JobSearchQuery(keywords=MARKETING, limit=100, **query_kwargs)
    return [p.title for p in filter_postings(postings, query)]


class TestObviousMatches:
    @pytest.mark.parametrize(
        "title",
        [
            "Performance Marketing Manager",
            "Senior Growth Marketing Lead",
            "Paid Media Specialist",
            "Demand Generation Manager",
            "Marketing Manager, EMEA",
        ],
    )
    def test_a_relevant_title_is_kept(self, title):
        assert kept([posting(title)]) == [title]


class TestObviousMismatches:
    @pytest.mark.parametrize(
        "title",
        [
            "Senior Backend Engineer",
            "Registered Nurse",
            "Warehouse Operative",
            "Financial Controller",
        ],
    )
    def test_an_unrelated_title_is_dropped(self, title):
        assert kept([posting(title)]) == []


class TestKeywordOnlyFalsePositives:
    def test_the_liquor_store_associate(self):
        # THE regression. One boilerplate mention of "performance" in the body
        # of a retail job. 987 postings like this passed the old filter.
        noise = posting(
            "Liquor Store Associate",
            description=(
                "We are a performance driven team. You will deliver excellent "
                "customer service and support store marketing activities."
            ),
        )
        assert kept([noise]) == []

    def test_a_single_word_body_hit_is_not_enough(self):
        vague = posting(
            "Operations Associate",
            description="You will work with the marketing team on occasion.",
        )
        assert kept([vague]) == []

    def test_a_multi_word_phrase_in_the_body_IS_enough(self):
        # The other direction: this recovers genuinely relevant roles whose
        # title is vague, without readmitting the noise above.
        real = posting(
            "Senior Manager, Digital",
            description="You will own performance marketing across paid channels.",
        )
        assert kept([real]) == ["Senior Manager, Digital"]

    def test_a_whole_word_match_is_required(self):
        # "cro" must not match "across".
        assert not keyword_matches_posting("cro", posting("Work across teams"))
        assert keyword_matches_posting("cro", posting("CRO Manager"))


class TestOtherMismatchAxes:
    def test_a_remote_only_search_drops_onsite_roles(self):
        onsite = posting("Performance Marketing Manager", remote=False, location="Berlin")
        assert kept([onsite], remote_only=True) == []

    def test_a_location_mismatch_is_dropped(self):
        berlin = posting("Performance Marketing Manager", location="Berlin, Germany")
        assert kept([berlin], locations=["London"]) == []

    def test_a_location_match_is_kept(self):
        london = posting("Performance Marketing Manager", location="London, UK")
        assert kept([london], locations=["London"]) == ["Performance Marketing Manager"]

    def test_a_salary_floor_drops_lower_paid_roles(self):
        low = posting(
            "Performance Marketing Manager",
            salary=Salary(min_amount=30000, max_amount=40000, currency="GBP"),
        )
        assert kept([low], min_salary=80000) == []

    def test_a_posting_with_no_salary_is_dropped_by_a_salary_floor(self):
        # Deliberate: an unknown salary cannot be asserted to clear a floor.
        unknown = posting("Performance Marketing Manager")
        assert kept([unknown], min_salary=80000) == []


class TestFilteringIsNotOverlyRestrictive:
    def test_a_realistic_mixed_feed_keeps_the_relevant_ones(self):
        feed = [
            posting("Performance Marketing Manager"),
            posting("Growth Marketing Lead"),
            posting("Paid Media Manager"),
            posting("Senior Backend Engineer"),
            posting("Liquor Store Associate", description="a performance driven culture"),
            posting("Warehouse Operative"),
            posting("Senior Manager, Digital", description="own demand generation end to end"),
        ]
        survivors = kept(feed)
        assert set(survivors) == {
            "Performance Marketing Manager",
            "Growth Marketing Lead",
            "Paid Media Manager",
            "Senior Manager, Digital",
        }

    def test_the_filter_is_not_so_tight_that_it_empties_a_good_feed(self):
        good = [posting(t) for t in ("Performance Marketing Manager", "Paid Media Manager")]
        assert len(kept(good)) == 2


class TestSeniorityAndIndustryAreScoredNotFiltered:
    """Seniority and industry are RANKING signals, not hard filters.

    Dropping a posting for seniority is how a filter goes from "precise" to
    "empty": titles are inconsistent enough that an "Associate" at one company
    is a "Manager" at another. So they lower the score rather than remove the
    row, and the user still gets to see them.
    """

    @pytest.fixture
    def brain(self):
        return CareerBrain(
            identity=Identity(full_name="Ada Lovelace", email="ada@example.com"),
            skills=[Skill(name="Google Ads"), Skill(name="Meta Ads (Facebook/Instagram)")],
            preferences=Preferences(desired_titles=["Performance Marketing Manager"]),
        )

    def test_a_title_match_scores_higher_than_a_seniority_mismatch(self, brain):
        wanted = posting("Performance Marketing Manager", description="Google Ads, Facebook")
        junior = posting("Marketing Intern", description="Google Ads, Facebook")
        assert score_posting(wanted, brain) > score_posting(junior, brain)

    def test_an_industry_mismatch_scores_lower_but_is_not_zero(self, brain):
        # It still uses her skills; the user decides.
        off_industry = posting("Performance Marketing Manager", description="Google Ads")
        assert score_posting(off_industry, brain) > 0

    def test_a_posting_using_none_of_her_skills_scores_low(self, brain):
        unrelated = posting("Performance Marketing Manager", description="COBOL and mainframes")
        relevant = posting("Performance Marketing Manager", description="Google Ads, Facebook")
        assert score_posting(unrelated, brain) < score_posting(relevant, brain)

    def test_a_remote_only_preference_penalises_onsite(self, brain):
        brain.preferences.remote_only = True
        onsite = posting("Performance Marketing Manager", remote=False, description="Google Ads")
        remote = posting("Performance Marketing Manager", remote=True, description="Google Ads")
        assert score_posting(onsite, brain) < score_posting(remote, brain)

    def test_scoring_works_with_no_llm_at_all(self, brain):
        # The heuristic score must stay functional without any AI provider —
        # AI is enrichment, never a dependency.
        assert 0.0 <= score_posting(posting("Performance Marketing Manager"), brain) <= 1.0
