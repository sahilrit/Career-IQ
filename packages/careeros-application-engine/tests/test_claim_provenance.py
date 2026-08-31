"""A Career Brain is the authority the fabrication checker measures against.

That is the whole reason provenance matters. An unsupported figure sitting in
the brain does not merely fail to help — it *launders* itself: the checker
built to catch invented numbers sees it as corroboration and waves the draft
through. Every test here pins one link in that chain.

The cases are real, from Sahil's own files:
  * $12M+ is BOOKED revenue; ~half came back as COD returns
  * $420K is a PEAK month; typical months ran $120-240K
  * delivered revenue is DISPUTED between ~$5.4M and ~$7.2M with no evidence
  * SEO and Google Analytics were claimed with no source support
"""

from __future__ import annotations

import pytest

from careeros_application_engine import (
    build_resume_content,
    check_disputed_claims,
    check_unqualified_figures,
    deterministic_review,
    render_resume_html,
    render_resume_markdown,
    render_resume_text,
)
from careeros_application_engine.cover_letter import TemplateCoverLetterGenerator
from careeros_career_brain import (
    Achievement,
    CareerBrain,
    ClaimStatus,
    Experience,
    Identity,
    Skill,
)
from careeros_job_providers import JobPosting


def achievement(description: str, metric: str, **kwargs) -> Achievement:
    return Achievement(description=description, metric=metric, **kwargs)


@pytest.fixture
def brain() -> CareerBrain:
    return CareerBrain(
        identity=Identity(
            full_name="Sahil Sachdeva",
            email="s@example.com",
            headline="Performance Marketing Manager",
            summary="Performance marketer focused on Meta Ads and CRO.",
        ),
        experiences=[
            Experience(
                company_name="Presha Trading",
                title="PPC Manager",
                start_date="2024-05-01",
                end_date="2025-05-01",
                achievements=[
                    achievement(
                        "Owned all paid media for a 4-5 store COD operation",
                        "$12M+ booked revenue at ~6.7x booked ROAS",
                        status=ClaimStatus.VERIFIED,
                        evidence="master §2A annual booked revenue ₹100Cr+",
                        qualifier="BOOKED revenue before COD returns",
                        requires_terms=["booked"],
                    ),
                    achievement(
                        "Scaled Meta spend against a profit target",
                        "$420K peak monthly spend; typical months $120-240K",
                        status=ClaimStatus.VERIFIED,
                        evidence="master §2A peak month ₹3.5Cr",
                        qualifier="PEAK month, not a typical month",
                        requires_terms=["peak", "single month"],
                    ),
                    achievement(
                        "Presha annual delivered revenue — DISPUTED",
                        "~$5.4M per one source vs ~$7.2M per another",
                        status=ClaimStatus.CONFLICTING,
                        evidence="40% vs 50-60% RTO; no primary evidence of the rate exists",
                    ),
                    achievement(
                        "Improved organic traffic via SEO",
                        "+25% organic traffic",
                        status=ClaimStatus.UNSUPPORTED,
                        evidence="no SEO work is recorded in any source document",
                    ),
                ],
            )
        ],
        skills=[Skill(name="Meta Ads")],
    )


@pytest.fixture
def posting() -> JobPosting:
    return JobPosting(
        source_provider="ats:greenhouse",
        external_id="1",
        title="Performance Marketing Manager",
        company_name="Globex",
        url="https://boards.greenhouse.io/globex/1",
        remote=True,
    )


def fabrications(draft: str, brain: CareerBrain) -> list:
    return [
        f
        for f in deterministic_review(draft, brain, allowed_extra={"Globex", "Sahil Sachdeva"})
        if f.severity.value == "fabrication"
    ]


class TestUnsupportedClaimsCannotLaunderThemselves:
    """The core defect: a figure in the brain is treated as true by the checker."""

    def test_an_unsupported_figure_is_flagged_like_an_invented_one(self, brain):
        # From the employer's side there is no difference between a number the
        # candidate made up and one his own records do not support.
        assert fabrications("I drove +25% organic traffic.", brain)

    def test_an_unsupported_claim_never_reaches_the_resume(self, brain, posting):
        text = render_resume_text(build_resume_content(brain, posting))
        assert "+25% organic traffic" not in text
        assert "organic traffic" not in text.lower()

    def test_it_is_absent_from_every_resume_format(self, brain, posting):
        content = build_resume_content(brain, posting)
        for rendered in (
            render_resume_text(content),
            render_resume_markdown(content),
            render_resume_html(content),
        ):
            assert "organic traffic" not in rendered.lower()

    def test_it_never_reaches_the_cover_letter(self, brain, posting):
        letter = TemplateCoverLetterGenerator().generate(brain, posting)
        assert "organic traffic" not in letter.lower()

    def test_the_claim_is_kept_in_the_profile_not_deleted(self, brain):
        # It is the user's own record of what they did. It is withheld from
        # employers, not erased from their history.
        seo = [a for a in brain.experiences[0].achievements if "SEO" in a.description]
        assert seo and seo[0].status is ClaimStatus.UNSUPPORTED
        assert seo[0].evidence


class TestDisputedClaimsAreNeverPublished:
    """The RTO conflict: ~$5.4M vs ~$7.2M, with no evidence either way."""

    @pytest.mark.parametrize("figure", ["$5.4M", "$7.2M"])
    def test_neither_side_of_the_dispute_may_be_stated(self, brain, figure):
        found = fabrications(f"I delivered {figure} in revenue.", brain)
        assert found, figure
        assert "disputed" in found[0].detail.lower()

    def test_the_finding_explains_why_it_is_disputed(self, brain):
        found = check_disputed_claims("I delivered $7.2M in revenue.", brain)
        assert "no primary evidence" in found[0].detail

    def test_a_disputed_claim_is_excluded_from_the_resume(self, brain, posting):
        text = render_resume_text(build_resume_content(brain, posting))
        assert "5.4M" not in text and "7.2M" not in text

    def test_both_versions_are_preserved_for_later_verification(self, brain):
        disputed = [
            a for a in brain.experiences[0].achievements if a.status is ClaimStatus.CONFLICTING
        ]
        assert disputed
        assert "5.4M" in disputed[0].metric and "7.2M" in disputed[0].metric


class TestQualifiedFiguresCannotBecomeUnqualifiedClaims:
    """$12M+ booked is true. $12M+ total revenue is not. Both contain $12M."""

    def test_booked_revenue_stated_as_total_revenue_is_flagged(self, brain):
        found = fabrications("I generated $12M+ in total revenue.", brain)
        assert found
        assert found[0].category == "unqualified figure"

    def test_the_same_figure_passes_when_properly_qualified(self, brain):
        assert not fabrications("I generated $12M+ in booked revenue.", brain)

    def test_a_peak_month_stated_as_a_monthly_average_is_flagged(self, brain):
        assert fabrications("I managed $420K+ in monthly ad spend.", brain)

    def test_the_peak_passes_when_called_a_peak(self, brain):
        assert not fabrications("Spend peaked at $420K in a single month.", brain)

    def test_the_finding_names_the_term_that_was_missing(self, brain):
        found = check_unqualified_figures("I generated $12M+ in revenue.", brain)
        assert "'booked'" in found[0].detail

    def test_the_resume_carries_the_qualifier_with_the_figure(self, brain, posting):
        text = render_resume_text(build_resume_content(brain, posting))
        if "$12M+" in text:
            assert "BOOKED" in text or "booked" in text


class TestFigureMatchingIsTokenBased:
    """ "3x" must not match inside "12.33x" — the substring trap that made the
    disputed delivered ROAS flag a verified best-month figure."""

    def test_a_disputed_figure_does_not_match_inside_a_larger_number(self, brain):
        brain.experiences[0].achievements.append(
            achievement(
                "Best month",
                "$570K at 12.33x",
                status=ClaimStatus.VERIFIED,
                requires_terms=["month"],
            )
        )
        assert not fabrications("My best month delivered $570K at 12.33x.", brain)


class TestBackwardCompatibility:
    """Adopting provenance must not silently empty existing résumés."""

    def test_an_unaudited_claim_still_publishes(self, brain, posting):
        brain.experiences[0].achievements.append(
            achievement("Legacy bullet with no audit", "+10% something")
        )
        text = render_resume_text(build_resume_content(brain, posting))
        assert "Legacy bullet" in text

    def test_unknown_is_publishable_but_conflicting_and_unsupported_are_not(self):
        assert ClaimStatus.UNKNOWN.is_publishable
        assert ClaimStatus.VERIFIED.is_publishable
        assert ClaimStatus.DERIVED.is_publishable
        assert not ClaimStatus.CONFLICTING.is_publishable
        assert not ClaimStatus.UNSUPPORTED.is_publishable

    def test_an_achievement_defaults_to_unknown(self):
        assert Achievement(description="x").status is ClaimStatus.UNKNOWN


class TestTheAiReviewerIsToldWhatIsNotAFact:
    def test_unsafe_claims_are_labelled_in_the_facts_given_to_the_reviewer(self, brain):
        from careeros_application_engine import profile_facts

        facts = profile_facts(brain)
        assert "NOT a usable fact" in facts
        # And the instruction that tells it what to do with them.
        assert "FABRICATION" in facts

    def test_supported_claims_carry_their_qualifier_into_the_facts(self, brain):
        from careeros_application_engine import profile_facts

        assert "BOOKED revenue before COD returns" in profile_facts(brain)


class TestQualifiersDoNotBleedAcrossFigures:
    """A truthful sentence must not be flagged.

    A false fabrication finding is the most expensive kind: it trains the user
    to ignore findings, which disarms the one layer standing between a
    hallucinated claim and a real application.

    Observed live: "$12M+ booked revenue ... on $1.4-2.2M annual spend" was one
    achievement, so the "booked" requirement attached to the REVENUE figure was
    applied to the SPEND figure too — and a correct sentence about spend was
    reported as a fabrication. Spend is spend; it needs no qualifier.
    """

    @pytest.fixture
    def brain_with_split_claims(self, brain):
        brain.experiences[0].achievements.append(
            achievement(
                "Managed the annual Meta budget",
                "$1.4-2.2M annual Meta ad spend",
                status=ClaimStatus.VERIFIED,
                evidence="master §2A annual ad spend ₹12-18Cr",
            )
        )
        return brain

    def test_a_truthful_spend_sentence_is_not_flagged(self, brain_with_split_claims):
        assert not fabrications(
            "I managed $1.4-2.2M in annual Meta spend.", brain_with_split_claims
        )

    def test_the_revenue_qualifier_still_applies_to_the_revenue_figure(
        self, brain_with_split_claims
    ):
        assert fabrications("I generated $12M+ in total revenue.", brain_with_split_claims)

    def test_an_unqualified_claim_is_not_rescued_by_a_neighbouring_claim(
        self, brain_with_split_claims
    ):
        # Mentioning spend correctly must not launder the revenue claim.
        assert fabrications(
            "I managed $1.4-2.2M in spend and generated $12M+ in total revenue.",
            brain_with_split_claims,
        )
