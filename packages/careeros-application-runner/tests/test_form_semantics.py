"""Semantic classification of form controls and fields.

Every case here is either a real form that broke the selector-matching
approach, or a label variant that a hardcoded selector list cannot cover.
"""

from __future__ import annotations

import pytest

from careeros_application_runner.form_semantics import (
    ControlKind,
    FieldPurpose,
    classify_control,
    classify_field,
    find_submit_control,
    map_fields,
)


def button(**kwargs) -> dict:
    return {
        "selector": kwargs.pop("selector", "[id='b']"),
        "text": "",
        "accessible_name": "",
        "role": "button",
        "type": "submit",
        "disabled": False,
        "near_file_input": False,
        "in_form": True,
        "form_field_count": 6,
        "surrounding_text": "",
        **kwargs,
    }


def field(**kwargs) -> dict:
    return {
        "selector": kwargs.pop("selector", "[id='f']"),
        "tag": "input",
        "type": "text",
        "name": "",
        "id_attr": "",
        "label": "",
        "aria_label": "",
        "placeholder": "",
        "autocomplete": "",
        "heading": "",
        "required": False,
        "disabled": False,
        "readonly": False,
        "options": [],
        **kwargs,
    }


class TestSubmitVsUpload:
    def test_ashby_upload_file_is_not_a_submit_button(self):
        # THE bug: on a real Ashby form every "Upload file" control renders as
        # button[type=submit], so a selector match clicked one of them and
        # opened a file dialog while believing it had applied.
        control = button(text="Upload file", accessible_name="Upload file", type="submit")
        assert classify_control(control) is ControlKind.UPLOAD

    def test_a_control_inside_a_file_widget_is_an_upload_whatever_it_says(self):
        # Unlabelled upload buttons exist. The DOM fact beats the label.
        control = button(text="Add", accessible_name="", near_file_input=True)
        assert classify_control(control) is ControlKind.UPLOAD

    @pytest.mark.parametrize(
        "label",
        ["Submit Application", "Submit application", "Send application", "Apply for this job"],
    )
    def test_explicit_submission_phrases(self, label):
        assert classify_control(button(accessible_name=label)) is ControlKind.SUBMIT_APPLICATION

    def test_a_bare_submit_label_submits(self):
        assert classify_control(button(accessible_name="Submit")) is ControlKind.SUBMIT_APPLICATION

    def test_submit_resume_uploads_rather_than_submits(self):
        # Contains "submit", is not a submission.
        assert classify_control(button(accessible_name="Submit resume")) is ControlKind.UPLOAD

    @pytest.mark.parametrize(
        ("label", "expected"),
        [
            ("Continue", ControlKind.CONTINUE),
            ("Next", ControlKind.NEXT),
            ("Next step", ControlKind.NEXT),
            ("Save draft", ControlKind.SAVE),
            ("Save and continue", ControlKind.CONTINUE),
            ("Review your application", ControlKind.REVIEW),
            ("Cancel", ControlKind.CANCEL),
            ("Go back", ControlKind.CANCEL),
            ("Yes", ControlKind.OTHER),
        ],
    )
    def test_the_other_kinds_are_distinguished(self, label, expected):
        assert classify_control(button(accessible_name=label)) is expected

    def test_save_and_continue_is_progress_not_a_draft_save(self):
        # Ordering matters: it contains both words.
        assert classify_control(button(accessible_name="Save & Continue")) is ControlKind.CONTINUE


class TestFindSubmitControl:
    def test_the_forty_button_ashby_form(self):
        # Thirty-nine upload/answer controls, one real submit, all of them
        # button[type=submit]. Selector matching picked the first.
        descriptors = [
            button(selector=f"[id='upload{i}']", accessible_name="Upload file") for i in range(20)
        ]
        descriptors += [button(selector=f"[id='yes{i}']", accessible_name="Yes") for i in range(19)]
        descriptors.append(button(selector="[id='real']", accessible_name="Submit Application"))
        found = find_submit_control(descriptors)
        assert found is not None
        assert found.selector == "[id='real']"
        assert found.kind is ControlKind.SUBMIT_APPLICATION

    def test_no_submit_control_returns_none_rather_than_a_guess(self):
        # "No submit button" is recoverable — a human finishes it. "We clicked
        # the wrong thing" is not.
        descriptors = [
            button(selector="[id='u']", accessible_name="Upload file"),
            button(selector="[id='n']", accessible_name="Next"),
        ]
        assert find_submit_control(descriptors) is None

    def test_a_header_cta_does_not_beat_the_real_button_at_the_bottom(self):
        descriptors = [
            button(selector="[id='top']", accessible_name="Apply now"),
            button(selector="[id='email']", accessible_name="Upload file"),
            button(selector="[id='bottom']", accessible_name="Submit Application"),
        ]
        assert find_submit_control(descriptors).selector == "[id='bottom']"

    def test_a_disabled_submit_is_reported_as_disabled_not_hidden(self):
        # Usually means a required field is still empty — which is actionable,
        # so it must not be silently skipped.
        found = find_submit_control(
            [button(selector="[id='s']", accessible_name="Submit Application", disabled=True)]
        )
        assert found is not None
        assert found.disabled
        assert "not complete" in found.reason

    def test_an_enabled_submit_wins_over_a_disabled_one(self):
        found = find_submit_control(
            [
                button(selector="[id='off']", accessible_name="Submit Application", disabled=True),
                button(selector="[id='on']", accessible_name="Submit Application"),
            ]
        )
        assert found.selector == "[id='on']"
        assert not found.disabled


class TestFieldPurpose:
    @pytest.mark.parametrize(
        "label",
        ["First Name", "First name", "Given Name", "Legal First Name", "Forename", "firstName"],
    )
    def test_first_name_variants(self, label):
        assert classify_field(field(label=label)) is FieldPurpose.FIRST_NAME

    @pytest.mark.parametrize(
        "label", ["Last Name", "Surname", "Family Name", "Legal Last Name", "last_name"]
    )
    def test_last_name_variants(self, label):
        assert classify_field(field(label=label)) is FieldPurpose.LAST_NAME

    @pytest.mark.parametrize(
        "label", ["Phone", "Mobile", "Telephone", "Contact Number", "Cell phone", "Mobile number"]
    )
    def test_phone_variants(self, label):
        assert classify_field(field(label=label)) is FieldPurpose.PHONE

    @pytest.mark.parametrize("label", ["LinkedIn", "LinkedIn URL", "LinkedIn Profile"])
    def test_linkedin_variants(self, label):
        assert classify_field(field(label=label)) is FieldPurpose.LINKEDIN

    @pytest.mark.parametrize(
        "label",
        ["Current Employer", "Current Company", "Present Employer", "Most recent company"],
    )
    def test_employer_variants(self, label):
        assert classify_field(field(label=label)) is FieldPurpose.CURRENT_EMPLOYER

    def test_first_language_is_not_a_first_name(self):
        # The exclusion list earning its keep: substring matching alone maps
        # this to FIRST_NAME and fills it with "Sahil".
        assert classify_field(field(label="First Language")) is FieldPurpose.QUESTION

    def test_company_name_is_an_employer_not_a_full_name(self):
        assert classify_field(field(label="Company Name")) is FieldPurpose.CURRENT_EMPLOYER

    def test_university_name_is_a_question_not_the_candidates_name(self):
        assert classify_field(field(label="University name")) is FieldPurpose.QUESTION

    def test_email_is_found_without_a_type_email_input(self):
        # Modern Greenhouse renders email as <input type="text" id="email"
        # autocomplete="email"> — no type="email" anywhere.
        descriptor = field(type="text", id_attr="email", autocomplete="email")
        assert classify_field(descriptor) is FieldPurpose.EMAIL

    def test_a_field_labelled_only_by_its_name_attribute_still_maps(self):
        assert classify_field(field(name="candidate_email")) is FieldPurpose.EMAIL

    def test_autocomplete_settles_it_on_its_own(self):
        assert classify_field(field(autocomplete="family-name")) is FieldPurpose.LAST_NAME

    def test_a_file_input_is_a_resume_by_default(self):
        assert classify_field(field(type="file", name="attachment")) is FieldPurpose.RESUME

    def test_a_cover_letter_file_input_is_not_the_resume_slot(self):
        # Uploading the résumé into the cover-letter slot is a real bug that
        # happened on forms carrying both file inputs.
        descriptor = field(type="file", name="cover_letter", label="Cover letter")
        assert classify_field(descriptor) is FieldPurpose.COVER_LETTER

    def test_a_real_screening_question_stays_a_question(self):
        descriptor = field(label="Why do you want to work here?", tag="textarea")
        assert classify_field(descriptor) is FieldPurpose.QUESTION

    def test_a_section_heading_does_not_label_every_field_under_it(self):
        # heading is section context, not a label. Treating it as one made
        # every field in "Contact details" look like a contact field.
        descriptor = field(heading="Contact details", label="How did you hear about us?")
        assert classify_field(descriptor) is FieldPurpose.QUESTION


class TestMapFields:
    def test_disabled_and_readonly_fields_are_dropped(self):
        # Writing to them cannot work; including them turns an impossible fill
        # into a reported failure a user cannot act on.
        rows = [
            field(selector="[id='a']", label="Email"),
            field(selector="[id='b']", label="Phone", disabled=True),
            field(selector="[id='c']", label="First Name", readonly=True),
        ]
        assert [m.selector for m in map_fields(rows)] == ["[id='a']"]

    def test_required_and_kind_are_carried_through(self):
        rows = [
            field(selector="[id='cv']", type="file", name="resume", required=True),
            field(selector="[id='s']", tag="select", options=["Yes", "No"], label="Sponsorship?"),
        ]
        mapped = map_fields(rows)
        assert mapped[0].kind == "file"
        assert mapped[0].required
        assert mapped[1].kind == "select"
        assert mapped[1].options == ["Yes", "No"]


class TestPhrasesMatchOnWordBoundaries:
    """Substring matching maps "Race / Ethnicity" to LOCATION.

    "city" is inside "ethni-CITY". The rules-based answerer already documents
    this exact trap; the field classifier had it too, and it silently swallowed
    every EEO question into the location field.
    """

    def test_ethnicity_is_not_a_location(self):
        assert classify_field(field(label="Race / Ethnicity")) is FieldPurpose.QUESTION

    def test_a_real_city_field_still_maps(self):
        assert classify_field(field(label="City")) is FieldPurpose.LOCATION
        assert classify_field(field(label="City or town")) is FieldPurpose.LOCATION

    @pytest.mark.parametrize(
        ("label", "expected"),
        [
            # Each of these embeds a rule phrase inside a longer word.
            ("Recovery plan", FieldPurpose.QUESTION),  # "cv" inside "reCoVery"? no — guard anyway
            ("Nickname preference", FieldPurpose.QUESTION),  # "name" inside "nickname"
            ("Telemetry experience", FieldPurpose.QUESTION),  # "tel" inside "telemetry"
            ("Countryside relocation", FieldPurpose.QUESTION),  # "country" inside "countryside"
        ],
    )
    def test_a_phrase_inside_a_longer_word_does_not_match(self, label, expected):
        assert classify_field(field(label=label)) is expected

    def test_a_hyphenated_email_label_still_maps(self):
        # Signal text normalises hyphens to spaces, so "e-mail" alone would
        # never have matched what the DOM actually produced.
        assert classify_field(field(label="E-mail address")) is FieldPurpose.EMAIL


class TestChoiceGroups:
    def test_radio_options_collapse_into_one_question(self):
        rows = [
            field(
                selector="[id='r1']",
                type="radio",
                name="race",
                label="Race / Ethnicity",
                option_label="Hispanic or Latino",
            ),
            field(
                selector="[id='r2']",
                type="radio",
                name="race",
                label="Race / Ethnicity",
                option_label="Decline to self-identify",
            ),
        ]
        mapped = map_fields(rows)
        assert len(mapped) == 1
        assert mapped[0].kind == "choice"
        assert mapped[0].label == "race / ethnicity"
        assert mapped[0].options == ["hispanic or latino", "decline to self-identify"]
        assert mapped[0].option_selectors["decline to self-identify"] == "[id='r2']"

    def test_two_different_groups_stay_separate(self):
        rows = [
            field(
                selector="[id='a']", type="radio", name="race", label="Race", option_label="Asian"
            ),
            field(
                selector="[id='b']",
                type="radio",
                name="veteran",
                label="Veteran status",
                option_label="I am a veteran",
            ),
        ]
        assert len(map_fields(rows)) == 2

    def test_a_group_is_required_if_any_of_its_controls_is(self):
        rows = [
            field(selector="[id='a']", type="radio", name="q", label="Q", option_label="Yes"),
            field(
                selector="[id='b']",
                type="radio",
                name="q",
                label="Q",
                option_label="No",
                required=True,
            ),
        ]
        assert map_fields(rows)[0].required

    def test_checkboxes_group_the_same_way(self):
        rows = [
            field(
                selector="[id='a']",
                type="checkbox",
                name="tools",
                label="Tools you use",
                option_label="Google Ads",
            ),
            field(
                selector="[id='b']",
                type="checkbox",
                name="tools",
                label="Tools you use",
                option_label="Meta Ads",
            ),
        ]
        mapped = map_fields(rows)
        assert len(mapped) == 1 and mapped[0].kind == "choice"
