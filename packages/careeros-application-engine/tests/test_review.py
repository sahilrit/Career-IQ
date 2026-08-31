"""The reviewer: catching what a drafter invents."""

from __future__ import annotations

from datetime import date

import pytest

from careeros_application_engine import (
    Severity,
    deterministic_review,
    parse_review_output,
    profile_facts,
    review_application_draft,
)
from careeros_career_brain import (
    Achievement,
    CareerBrain,
    Education,
    Experience,
    Identity,
    Skill,
)


@pytest.fixture
def brain() -> CareerBrain:
    return CareerBrain(
        identity=Identity(
            full_name="Ada Lovelace",
            email="ada@example.com",
            headline="Performance marketer",
            summary="I run paid acquisition programmes.",
        ),
        experiences=[
            Experience(
                company_name="Northwind Trading",
                title="Performance Marketing Manager",
                start_date=date(2022, 1, 1),
                achievements=[
                    Achievement(description="Cut cost per acquisition", metric="31%"),
                ],
            )
        ],
        education=[Education(institution="Open University", credential="BSc Mathematics")],
        skills=[Skill(name="Meta Ads"), Skill(name="Google Ads")],
    )


def categories(findings) -> set[str]:
    return {f.category for f in findings}


class TestFabricatedEmployers:
    def test_an_employer_the_profile_never_mentions_is_flagged(self, brain):
        draft = "At Globex Corporation I led the paid media team."
        findings = deterministic_review(draft, brain)
        assert "unknown employer" in categories(findings)
        assert findings[0].severity is Severity.FABRICATION
        assert findings[0].evidence == "Globex Corporation"

    def test_a_real_employer_is_not_flagged(self, brain):
        findings = deterministic_review("At Northwind Trading I ran acquisition.", brain)
        assert "unknown employer" not in categories(findings)

    def test_the_company_being_applied_to_is_allowed(self, brain):
        # A cover letter naming its recipient is correct, not fabricated.
        draft = "I would love to work at Stripe on growth."
        findings = deterministic_review(draft, brain, allowed_extra={"Stripe"})
        assert "unknown employer" not in categories(findings)

    def test_prepositional_phrases_are_not_read_as_employers(self, brain):
        draft = "I work at scale and for the long term, at least in my last role."
        assert "unknown employer" not in categories(deterministic_review(draft, brain))

    def test_a_profile_with_no_employers_flags_any_named_one(self):
        empty = CareerBrain(identity=Identity(full_name="New Grad", email="n@e.com"))
        findings = deterministic_review("At Initech I built dashboards.", empty)
        assert "unknown employer" in categories(findings)


class TestFabricatedMetrics:
    def test_an_invented_percentage_is_flagged(self, brain):
        findings = deterministic_review("I grew revenue by 340% in a year.", brain)
        assert "unsupported metric" in categories(findings)
        assert any(f.evidence == "340%" for f in findings)

    def test_a_metric_the_profile_records_is_not_flagged(self, brain):
        # The profile records a 31% CPA cut, so quoting it is truthful.
        findings = deterministic_review("I cut cost per acquisition by 31%.", brain)
        assert "unsupported metric" not in categories(findings)

    def test_an_invented_budget_is_flagged(self, brain):
        findings = deterministic_review("I managed $2M in annual ad spend.", brain)
        assert "unsupported metric" in categories(findings)

    def test_a_draft_with_no_numbers_produces_no_metric_findings(self, brain):
        findings = deterministic_review("I run paid acquisition programmes.", brain)
        assert "unsupported metric" not in categories(findings)


class TestFabricatedCredentials:
    def test_a_degree_the_profile_lacks_is_flagged(self, brain):
        findings = deterministic_review("I hold an MBA from a top school.", brain)
        assert "unsupported credential" in categories(findings)

    def test_a_recorded_degree_is_not_flagged(self, brain):
        findings = deterministic_review("I completed a BSc in Mathematics.", brain)
        assert "unsupported credential" not in categories(findings)

    def test_a_profile_with_no_education_says_so_explicitly(self):
        empty = CareerBrain(identity=Identity(full_name="X", email="x@e.com"))
        findings = deterministic_review("I have a PhD in statistics.", empty)
        detail = next(f.detail for f in findings if f.category == "unsupported credential")
        assert "no education at all" in detail


class TestPlaceholders:
    @pytest.mark.parametrize(
        "draft",
        [
            "Dear [Hiring Manager], I am excited.",
            "I want to join {{company}}.",
            "I have XX years of experience.",
            "TODO: add the closing paragraph.",
        ],
    )
    def test_unreplaced_scaffolding_is_caught(self, draft, brain):
        findings = deterministic_review(draft, brain)
        assert any(f.severity is Severity.ERROR for f in findings)

    def test_an_empty_draft_is_an_error(self, brain):
        findings = deterministic_review("   ", brain)
        assert findings[0].category == "empty draft"


class TestReviewVerdict:
    def test_a_clean_draft_is_safe_to_send(self, brain):
        draft = "At Northwind Trading I cut cost per acquisition by 31% using Meta Ads."
        review = review_application_draft(draft, brain)
        assert review.is_safe_to_send
        assert review.findings == []

    def test_a_fabrication_blocks_sending(self, brain):
        review = review_application_draft("At Globex I tripled revenue by 340%.", brain)
        assert not review.is_safe_to_send
        assert len(review.fabrications) >= 1

    def test_a_warning_alone_does_not_block(self, brain):
        review = review_application_draft("At Northwind Trading I did good work.", brain)
        assert review.is_safe_to_send

    def test_no_ai_reviewer_is_reported_as_a_partial_review(self, brain):
        # "No findings" must not read as an all-clear when only half the review ran.
        review = review_application_draft("At Northwind Trading I worked.", brain)
        assert review.ai_reviewed is False
        assert "deterministic checks only" in review.summary()


class TestAiReviewer:
    def test_findings_from_the_reviewer_are_merged_in(self, brain):
        class Reviewer:
            def complete(self, *, system, prompt):
                return "WARNING|vague filler|says nothing specific|did good work"

        review = review_application_draft(
            "At Northwind Trading I did good work.", brain, ai_client=Reviewer()
        )
        assert review.ai_reviewed
        assert "vague filler" in categories(review.findings)

    def test_an_unavailable_reviewer_degrades_rather_than_fails(self, brain):
        class Broken:
            def complete(self, *, system, prompt):
                raise RuntimeError("no provider")

        review = review_application_draft("At Globex I did work.", brain, ai_client=Broken())
        # The deterministic half still caught the fabricated employer.
        assert not review.ai_reviewed
        assert "unknown employer" in categories(review.findings)

    def test_the_reviewer_is_given_the_facts_it_must_check_against(self, brain):
        facts = profile_facts(brain)
        assert "Northwind Trading" in facts
        assert "Open University" in facts

    def test_a_profile_with_nothing_recorded_says_so_in_the_facts(self):
        empty = CareerBrain(identity=Identity(full_name="X", email="x@e.com"))
        facts = profile_facts(empty)
        # Stating the absence explicitly is what stops a reviewer treating an
        # empty section as "unknown, therefore probably fine".
        assert "NONE RECORDED" in facts


class TestParsingReviewOutput:
    def test_parses_the_pipe_format(self):
        findings = parse_review_output(
            "FABRICATION|unknown employer|Globex is not in the profile|At Globex"
        )
        assert findings[0].severity is Severity.FABRICATION
        assert findings[0].evidence == "At Globex"

    def test_none_means_no_findings(self):
        assert parse_review_output("NONE") == []

    def test_praise_is_not_read_as_a_finding_or_as_approval(self):
        # A reviewer that says "looks good" has not reviewed; it yields nothing
        # structured rather than an endorsement.
        assert parse_review_output("This looks good to me!") == []

    def test_tolerates_bullets_and_stray_lines(self):
        text = "Here are my findings:\n- ERROR|placeholder|bracket text remains|[Company]\n"
        findings = parse_review_output(text)
        assert len(findings) == 1 and findings[0].category == "placeholder"

    def test_an_unknown_severity_is_skipped(self):
        assert parse_review_output("CRITICAL|x|y|z") == []


class TestPackageIntegration:
    def test_a_generated_package_carries_a_review(self, brain):
        from careeros_application_engine import build_application_package
        from careeros_job_providers import JobPosting

        posting = JobPosting(
            source_provider="ats:greenhouse",
            external_id="1",
            title="Growth Marketing Manager",
            company_name="Stripe",
            url="https://example.com/1",
        )
        package = build_application_package(brain, posting)
        assert package.review is not None
        # The company applied to is in the letter legitimately.
        assert "Stripe" not in {f.evidence for f in package.review.fabrications}

    def test_an_unreviewed_package_is_not_treated_as_safe(self, brain):
        from careeros_application_engine import build_application_package
        from careeros_job_providers import JobPosting

        posting = JobPosting(
            source_provider="ats:greenhouse",
            external_id="1",
            title="Growth Marketing Manager",
            company_name="Stripe",
            url="https://example.com/1",
        )
        package = build_application_package(brain, posting, review=False)
        # Absence of findings and absence of checking must not look the same.
        assert package.review is None
        assert package.is_safe_to_send is False

    def test_a_fabricating_generator_is_caught_before_the_package_is_returned(self, brain):
        from careeros_application_engine import build_application_package
        from careeros_job_providers import JobPosting

        class FabricatingGenerator:
            def generate(self, brain, posting):
                return "At Globex Corporation I grew revenue 340% and earned an MBA."

        posting = JobPosting(
            source_provider="ats:greenhouse",
            external_id="1",
            title="Growth Marketing Manager",
            company_name="Stripe",
            url="https://example.com/1",
        )
        package = build_application_package(
            brain, posting, cover_letter_generator=FabricatingGenerator()
        )
        assert not package.is_safe_to_send
        assert len(package.review.fabrications) >= 3
