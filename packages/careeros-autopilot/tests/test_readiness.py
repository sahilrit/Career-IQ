"""Readiness: "Application failed." is not an acceptable output.

Every attempt must say what happened, why, what was completed, what remains,
and whether a human has to act — and must leave behind enough evidence to
reproduce it without leaking the candidate's data.
"""

from __future__ import annotations

from careeros_application_engine import UnansweredQuestion
from careeros_application_runner import (
    FieldOutcome,
    FieldResult,
    FillReport,
    FormFieldMapping,
    QuestionField,
)
from careeros_autopilot import ApplicationRecommendation, ApplicationRoute
from careeros_autopilot.readiness import CheckState, assess_readiness


def mapping(**kwargs) -> FormFieldMapping:
    defaults = {
        "email_selector": "#email",
        "first_name_selector": "#first",
        "last_name_selector": "#last",
        "submit_selector": "#go",
        "success_selector": "#done",
    }
    return FormFieldMapping(**{**defaults, **kwargs})


def filled_report(*extra: FieldResult) -> FillReport:
    report = FillReport()
    for name in ("first_name", "last_name", "email"):
        report.add(
            FieldResult(field=name, selector=f"#{name}", outcome=FieldOutcome.FILLED, required=True)
        )
    for result in extra:
        report.add(result)
    return report


def complete_attempt(**overrides):
    kwargs = {
        "posting_url": "https://boards.greenhouse.io/acme/jobs/1",
        "application_url": "https://boards.greenhouse.io/acme/jobs/1",
        "ats": "greenhouse",
        "route": ApplicationRoute.ATS_HOSTED,
        "mapping": mapping(),
        "fill_report": filled_report(),
        "cover_letter": "Dear Acme…",
    }
    kwargs.update(overrides)
    return assess_readiness(**kwargs)


class TestScore:
    def test_a_complete_attempt_is_submission_ready_at_full_score(self):
        readiness = complete_attempt()
        assert readiness.is_submission_ready
        assert readiness.score == 100
        assert not readiness.blockers

    def test_a_skipped_stage_does_not_cost_score(self):
        # A form with no cover-letter field is not 10% worse than one with it.
        readiness = complete_attempt()
        states = {c.name: c.state for c in readiness.checks}
        assert states["Cover letter ready"] is CheckState.SKIPPED
        assert readiness.score == 100

    def test_a_warning_is_half_credit_and_does_not_block(self):
        report = filled_report(
            FieldResult(
                field="phone",
                selector="#phone",
                outcome=FieldOutcome.NEEDS_HUMAN,
                detail="no truthful value available from the profile",
            )
        )
        readiness = complete_attempt(fill_report=report)
        assert readiness.is_submission_ready
        assert 0 < readiness.score < 100
        assert [c.name for c in readiness.needs_review] == ["Profile fields available"]

    def test_a_missing_required_field_fails_and_blocks(self):
        report = filled_report(
            FieldResult(
                field="work_auth",
                selector="#wa",
                outcome=FieldOutcome.NEEDS_HUMAN,
                detail="your work-authorization status is not recorded",
                required=True,
            )
        )
        readiness = complete_attempt(fill_report=report)
        assert not readiness.is_submission_ready
        assert "Required fields filled" in [c.name for c in readiness.blockers]

    def test_an_attempt_that_never_reached_a_form_scores_low_not_zero_stages(self):
        readiness = assess_readiness(
            posting_url="https://boards.greenhouse.io/acme/jobs/1",
            error="the site is showing a bot-protection challenge",
        )
        assert not readiness.is_submission_ready
        assert readiness.score < 50
        # Every stage still appears, so it is visible WHERE it stopped.
        assert len(readiness.checks) == 10


class TestTheReportIsActionable:
    def test_a_failure_says_what_happened_why_and_what_remains(self):
        readiness = assess_readiness(
            posting_url="https://jobs.smartrecruiters.com/acme/1",
            application_url="https://jobs.smartrecruiters.com/acme/1",
            ats="smartrecruiters",
            route=ApplicationRoute.ATS_HOSTED,
            error="the form is inside an iframe that could not be reached",
        )
        text = readiness.failure_report()
        # An attempt that never reached the form is BLOCKED, which is a
        # different thing from one we filled but could not finish.
        assert "Application blocked." in text
        assert "Reason:" in text
        assert "iframe" in text
        assert "Status:" in text
        assert "Required action:" in text
        # The single most important line.
        assert "No application was submitted." in text

    def test_a_ready_application_says_so_and_still_lists_the_stages(self):
        text = complete_attempt().failure_report()
        assert "Application ready for you to submit." in text
        assert "Review and submit" in text
        assert "✓ Job identified" in text

    def test_the_percentage_never_appears_without_the_checklist(self):
        # A bare number is no more useful than "failed".
        report = complete_attempt().report()
        # Labelled "Form readiness" now: it measures the FORM, not whether the
        # application should be sent — that is the recommendation above it.
        assert "Form readiness: 100%" in report
        assert "✓ Required fields filled" in report
        assert report.splitlines()[0] == "READY TO APPLY"

    def test_unanswered_questions_are_listed_with_why_and_what_is_needed(self):
        readiness = complete_attempt(
            mapping=mapping(
                question_fields=[
                    QuestionField(selector="#wa", question="Authorized to work in the US?")
                ]
            ),
            unanswered=[
                UnansweredQuestion(
                    question="Authorized to work in the US?",
                    why="your work-authorization status is not recorded",
                    needs="set it in your Career Brain preferences",
                )
            ],
        )
        report = readiness.report()
        assert "Authorized to work in the US?" in report
        assert "why: your work-authorization status is not recorded" in report
        assert "needs: set it" in report

    def test_an_optional_unanswered_question_warns_rather_than_blocks(self):
        readiness = complete_attempt(
            mapping=mapping(
                question_fields=[QuestionField(selector="#q", question="Anything else?")]
            ),
            unanswered=[UnansweredQuestion(question="Anything else?", why="w", needs="n")],
        )
        assert readiness.is_submission_ready
        assert "Questions answered" in [c.name for c in readiness.needs_review]

    def test_a_required_unanswered_question_blocks(self):
        readiness = complete_attempt(
            mapping=mapping(
                question_fields=[
                    QuestionField(selector="#wa", question="Authorized to work?", required=True)
                ]
            ),
            unanswered=[UnansweredQuestion(question="Authorized to work?", why="w", needs="n")],
        )
        assert not readiness.is_submission_ready


class TestEvidence:
    def test_it_records_what_is_needed_to_reproduce_the_attempt(self):
        readiness = complete_attempt(
            screenshot="/tmp/shot.png", form_context="an iframe (url~/apply)"
        )
        evidence = readiness.evidence.as_dict()
        assert evidence["job_url"].endswith("/jobs/1")
        assert evidence["ats"] == "greenhouse"
        assert evidence["route"] == "ats_hosted"
        assert evidence["screenshot"] == "/tmp/shot.png"
        assert evidence["form_context"] == "an iframe (url~/apply)"
        assert evidence["captured_at"]
        # The recommendation, not the bare technical verdict — "ready to
        # apply" answers the question a reader of the evidence actually has.
        assert evidence["final_state"] == "ready_to_apply"

    def test_it_records_field_names_and_never_field_values(self):
        # Evidence has to be safe to attach to a bug report. Storing the values
        # would make every debug log a copy of the user's profile.
        readiness = complete_attempt()
        blob = repr(readiness.evidence.as_dict())
        assert "email" in blob  # the field NAME
        assert "@" not in blob or "example" not in blob  # no address values
        assert "Dear Acme" not in blob  # not the cover letter either

    def test_fields_not_on_the_form_are_recorded_as_unmapped(self):
        report = filled_report(
            FieldResult(
                field="cover_letter",
                selector="",
                outcome=FieldOutcome.NOT_PRESENT,
                detail="no selector for this field on this form",
            )
        )
        evidence = complete_attempt(fill_report=report).evidence
        assert "cover_letter" in evidence.unmapped_fields
        assert "cover_letter" not in evidence.mapped_fields


class TestExternalEmployerIsNotOurFailure:
    def test_an_employer_redirect_is_named_as_such_in_the_checklist(self):
        readiness = assess_readiness(
            posting_url="https://boards.greenhouse.io/stripe/jobs/1",
            route=ApplicationRoute.EXTERNAL_UNSUPPORTED,
        )
        detail = next(c.detail for c in readiness.checks if c.name == "Application URL found")
        assert "own site" in detail


class TestApplicationRecommendation:
    """Technical readiness and "should you apply" are different questions.

    They used to share one field. OpenAI's posting reached SUBMISSION_READY at
    83% while being explicitly restricted to US-based candidates: both facts
    were reported, but a human skimming — or any automation keying off
    "submission ready" — could act on the technical verdict and never see the
    disqualification.
    """

    def test_fillable_and_no_disqualifier_is_ready_to_apply(self):
        readiness = complete_attempt()
        assert readiness.recommendation is ApplicationRecommendation.READY_TO_APPLY
        assert readiness.may_submit
        assert readiness.is_submission_ready

    def test_fillable_but_disqualified_says_do_not_apply(self):
        readiness = complete_attempt(disqualifier="role is restricted to US-based candidates")
        assert (
            readiness.recommendation is ApplicationRecommendation.SUBMISSION_READY_BUT_DISQUALIFIED
        )
        # The technical fact is retained, unchanged, underneath.
        assert readiness.is_submission_ready
        assert readiness.score == 100

    def test_a_disqualified_application_may_never_be_submitted(self):
        # THE guard. Automation asks may_submit, never is_submission_ready.
        readiness = complete_attempt(disqualifier="role is restricted to US-based candidates")
        assert not readiness.may_submit
        assert readiness.is_submission_ready  # ...even though this is True

    def test_blocked_wins_over_a_disqualifier_but_still_surfaces_it(self):
        readiness = assess_readiness(
            posting_url="https://boards.greenhouse.io/acme/jobs/1",
            error="the site is showing a bot-protection challenge",
            disqualifier="role is restricted to US-based candidates",
        )
        assert readiness.recommendation is ApplicationRecommendation.BLOCKED
        assert not readiness.may_submit
        assert readiness.is_disqualified
        assert "US-based" in readiness.report()

    def test_a_missing_required_field_is_needs_user_input(self):
        report = filled_report(
            FieldResult(
                field="work_auth",
                selector="#wa",
                outcome=FieldOutcome.NEEDS_HUMAN,
                detail="not recorded",
                required=True,
            )
        )
        readiness = complete_attempt(fill_report=report)
        assert readiness.recommendation is ApplicationRecommendation.NEEDS_USER_INPUT
        assert not readiness.may_submit

    def test_only_ready_to_apply_permits_submission(self):
        permitted = [r for r in ApplicationRecommendation if r.may_submit]
        assert permitted == [ApplicationRecommendation.READY_TO_APPLY]


class TestTheDisqualificationCannotBeSkimmedPast:
    def test_the_report_leads_with_do_not_apply(self):
        readiness = complete_attempt(disqualifier="role is restricted to US-based candidates")
        first_line = readiness.report().splitlines()[0]
        assert "DO NOT APPLY" in first_line

    def test_the_percentage_no_longer_comes_first(self):
        # Leading with "83%" is what let a reader take it as approval.
        readiness = complete_attempt(disqualifier="US-only role")
        assert not readiness.report().splitlines()[0].startswith("Application readiness")

    def test_the_reason_appears_next_to_the_headline(self):
        readiness = complete_attempt(disqualifier="role is restricted to US-based candidates")
        assert "restricted to US-based candidates" in readiness.report()

    def test_the_failure_report_says_do_not_submit(self):
        readiness = complete_attempt(disqualifier="US-only role")
        text = readiness.failure_report()
        assert "DO NOT APPLY" in text
        assert "Do not submit this one" in text
        assert "Review and submit — nothing is missing." not in text

    def test_a_clean_application_still_says_review_and_submit(self):
        assert "Review and submit" in complete_attempt().failure_report()

    def test_the_evidence_records_the_recommendation_not_just_readiness(self):
        readiness = complete_attempt(disqualifier="US-only role")
        assert readiness.evidence.as_dict()["final_state"] == "submission_ready_but_disqualified"
