"""Fill verification: telling a fill that worked from one that looked like it did."""

from __future__ import annotations

import pytest

from careeros_application_engine import ApplicationPackage, ATSReport, ResumeContent
from careeros_application_runner import (
    FieldOutcome,
    FormFieldMapping,
    QuestionField,
    fill_application_form,
)
from careeros_browser import FakeBrowserSession


def make_package(*, phone: str | None = "+44 20 7946 0000", cover_letter: str = "Dear team,"):
    return ApplicationPackage(
        resume_content=ResumeContent(
            full_name="Ada Lovelace",
            headline="Growth marketer",
            email="ada@example.com",
            phone=phone,
            location="London, UK",
        ),
        resume_text="Ada Lovelace — Growth marketer",
        resume_markdown="# Ada Lovelace",
        resume_html="<h1>Ada Lovelace</h1>",
        cover_letter=cover_letter,
        answers={},
        ats_report=ATSReport(covered_keywords=[], missing_keywords=[]),
    )


@pytest.fixture
def package() -> ApplicationPackage:
    return make_package()


@pytest.fixture
def session() -> FakeBrowserSession:
    return FakeBrowserSession()


def base_mapping(**kwargs) -> FormFieldMapping:
    defaults = {
        "first_name_selector": "#first_name",
        "last_name_selector": "#last_name",
        "email_selector": "#email",
        "phone_selector": "#phone",
        "submit_selector": "#submit",
        "success_selector": "#done",
    }
    defaults.update(kwargs)
    return FormFieldMapping(**defaults)


def outcome_for(report, field: str) -> FieldOutcome:
    return next(r.outcome for r in report.results if r.field == field)


def detail_for(report, field: str) -> str:
    return next(r.detail for r in report.results if r.field == field)


class TestHappyPath:
    def test_fills_and_verifies_the_core_fields(self, session, package):
        report = fill_application_form(session, package, base_mapping())
        assert outcome_for(report, "first_name") is FieldOutcome.FILLED
        assert outcome_for(report, "email") is FieldOutcome.FILLED
        assert session.field_value("#email") == "ada@example.com"
        assert report.is_submittable

    def test_splits_the_name_across_two_inputs(self, session, package):
        fill_application_form(session, package, base_mapping())
        assert session.field_value("#first_name") == "Ada"
        assert session.field_value("#last_name") == "Lovelace"

    def test_uses_a_single_full_name_field_when_that_is_what_the_form_has(self, session, package):
        mapping = base_mapping(
            first_name_selector=None, last_name_selector=None, full_name_selector="#name"
        )
        fill_application_form(session, package, mapping)
        assert session.field_value("#name") == "Ada Lovelace"

    def test_summary_is_human_readable(self, session, package):
        report = fill_application_form(session, package, base_mapping())
        assert "filled" in report.summary()


class TestSilentRejection:
    """The failure this whole module exists for."""

    def test_a_field_that_discards_the_value_is_a_reported_failure(self, session, package):
        # A React-controlled or disabled input accepts fill() without error and
        # then holds nothing. The old code called that success.
        session.set_field_rejects("#email")
        report = fill_application_form(session, package, base_mapping())
        assert outcome_for(report, "email") is FieldOutcome.FAILED
        assert "discarded" in detail_for(report, "email")

    def test_a_silently_rejected_required_field_blocks_submission(self, session, package):
        session.set_field_rejects("#email")
        report = fill_application_form(session, package, base_mapping())
        assert not report.is_submittable
        assert "email" in {r.field for r in report.failures}

    def test_an_unreadable_field_is_a_failure_not_a_silent_pass(self, session, package):
        session.set_field_unreadable("#email")
        report = fill_application_form(session, package, base_mapping())
        assert outcome_for(report, "email") is FieldOutcome.FAILED
        assert "read the field back" in detail_for(report, "email")


class TestNoFabrication:
    def test_a_missing_phone_is_handed_to_a_human_not_invented(self, session):
        report = fill_application_form(session, make_package(phone=None), base_mapping())
        assert outcome_for(report, "phone") is FieldOutcome.NEEDS_HUMAN
        assert session.field_value("#phone") is None

    def test_an_unanswered_question_is_left_blank_and_reported(self, session, package):
        mapping = base_mapping(
            question_fields=[
                QuestionField(selector="#visa", question="Do you need sponsorship?", required=True)
            ]
        )
        report = fill_application_form(session, package, mapping, question_answers={})
        assert outcome_for(report, "Do you need sponsorship?") is FieldOutcome.NEEDS_HUMAN
        # Required and unanswered, so it must block rather than be submitted blank.
        assert not report.is_submittable
        assert [r.field for r in report.blocking] == ["Do you need sponsorship?"]

    def test_an_optional_unanswered_question_does_not_block(self, session, package):
        mapping = base_mapping(
            question_fields=[QuestionField(selector="#hear", question="How did you hear about us?")]
        )
        report = fill_application_form(session, package, mapping, question_answers={})
        assert report.is_submittable


class TestFieldKinds:
    def test_a_file_upload_is_unverified_rather_than_falsely_confirmed(
        self, session, package, tmp_path
    ):
        resume = tmp_path / "cv.pdf"
        resume.write_bytes(b"%PDF-1.4")
        mapping = base_mapping(resume_upload_selector="#resume")
        report = fill_application_form(session, package, mapping, resume_file_path=str(resume))
        # input_value() is meaningless for a file input, so claiming FILLED
        # would be a lie; the human is told to eyeball it instead.
        assert outcome_for(report, "resume") is FieldOutcome.UNVERIFIED
        assert session.uploaded_files["#resume"] == str(resume)

    def test_a_missing_resume_for_a_required_upload_blocks(self, session, package):
        mapping = base_mapping(resume_upload_selector="#resume")
        report = fill_application_form(session, package, mapping, resume_file_path=None)
        assert outcome_for(report, "resume") is FieldOutcome.NEEDS_HUMAN
        assert not report.is_submittable

    def test_a_combobox_question_is_selected_not_typed(self, session, package):
        session.set_comboboxes([{"selector": "#country", "question": "Country"}])
        session.set_combobox_options("#country", ["United States", "United Kingdom"])
        mapping = base_mapping(
            question_fields=[
                QuestionField(selector="#country", question="Country", kind="combobox")
            ]
        )
        report = fill_application_form(
            session, package, mapping, question_answers={"#country": "United Kingdom"}
        )
        assert outcome_for(report, "Country") is FieldOutcome.FILLED
        assert session.combobox_selections == [("#country", "United Kingdom")]

    def test_a_combobox_with_no_match_fails_loudly_rather_than_guessing(self, session, package):
        # Picking a plausible-but-wrong work-authorization option is far worse
        # than leaving it for a human.
        session.set_combobox_options("#country", ["Germany", "France"])
        mapping = base_mapping(
            question_fields=[
                QuestionField(selector="#country", question="Country", kind="combobox")
            ]
        )
        report = fill_application_form(
            session, package, mapping, question_answers={"#country": "United Kingdom"}
        )
        assert outcome_for(report, "Country") is FieldOutcome.FAILED


class TestAbsentFields:
    def test_a_field_the_form_does_not_have_is_not_a_failure(self, session, package):
        mapping = base_mapping(cover_letter_selector=None)
        report = fill_application_form(session, package, mapping)
        assert report.is_submittable

    def test_a_cover_letter_field_with_no_letter_is_not_blocking(self, session):
        mapping = base_mapping(cover_letter_selector="#cover")
        report = fill_application_form(session, make_package(cover_letter=""), mapping)
        assert outcome_for(report, "cover_letter") is FieldOutcome.NEEDS_HUMAN
        assert report.is_submittable


class TestReformattedValues:
    """A field that reformats what it stores has still been filled."""

    def test_a_phone_mask_that_changes_formatting_is_not_a_failure(self, session):
        # Verified against a live Workable form: "+91 91298 32709" is stored as
        # "091298 32709". Calling that a failed fill blocked otherwise-complete
        # applications on a field that was correctly filled.
        from careeros_application_runner.fill import _same_number

        assert _same_number("+91 91298 32709", "091298 32709")

    def test_a_different_number_is_still_a_failure(self):
        from careeros_application_runner.fill import _same_number

        assert not _same_number("+91 91298 32709", "+1 415 555 0100")

    def test_short_codes_do_not_coincidentally_match(self):
        from careeros_application_runner.fill import _same_number

        assert not _same_number("123", "0123")

    def test_a_reformatting_field_reports_as_filled_end_to_end(self, session, package):
        # Simulate the mask by rewriting the stored value as the field would.
        original_fill = session.fill

        def masking_fill(selector, value):
            original_fill(selector, "091298 32709" if selector == "#phone" else value)

        session.fill = masking_fill
        report = fill_application_form(
            session, make_package(phone="+91 91298 32709"), base_mapping()
        )
        assert outcome_for(report, "phone") is FieldOutcome.FILLED


class TestOptionalFailuresDoNotBlock:
    def test_an_optional_field_that_failed_is_reported_but_does_not_block(self, session, package):
        # The fields that most often fail on a live Greenhouse form are the
        # optional EEO demographic dropdowns. Treating those as blockers held
        # back applications that were otherwise complete.
        session.set_combobox_options("#gender", [])
        mapping = base_mapping(
            question_fields=[QuestionField(selector="#gender", question="Gender", kind="combobox")]
        )
        report = fill_application_form(
            session, package, mapping, question_answers={"#gender": "Prefer not to say"}
        )
        assert outcome_for(report, "Gender") is FieldOutcome.FAILED
        assert report.failures  # still surfaced to a human
        assert report.is_submittable  # but does not hold the application back

    def test_a_required_field_that_failed_still_blocks(self, session, package):
        session.set_field_rejects("#email")
        report = fill_application_form(session, package, base_mapping())
        assert not report.is_submittable
