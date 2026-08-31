"""The selector traps that have actually shipped, pinned so they cannot return.

Each of these was a live bug that produced NO error — just silently wrong or
empty results — which is precisely why they survived so long. A silent
extraction bug looks identical to "the site had nothing on it".
"""

from __future__ import annotations

import pytest

from careeros_browser import PlaywrightBrowserSession

pytestmark = pytest.mark.browser


@pytest.fixture(scope="module")
def browser():
    playwright_api = pytest.importorskip("playwright.sync_api")
    try:
        with playwright_api.sync_playwright() as playwright:
            instance = playwright.chromium.launch(headless=True)
            yield instance
            instance.close()
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"Chromium is not available: {exc}")


@pytest.fixture
def page_with(browser):
    pages = []

    def _open(html: str):
        page = browser.new_page()
        pages.append(page)
        page.set_content(html)
        return PlaywrightBrowserSession(page)

    yield _open
    for page in pages:
        page.close()


LINKS = """
<a href="/one">One</a>
<a href="/two">Two</a>
<div class="card"><a href="/nested">Nested</a></div>
"""


class TestAttributeExtraction:
    """The ``"a@href"`` bug: apply-link discovery never worked, on any site."""

    def test_a_bare_at_attribute_reads_the_matched_elements_own_attribute(self, page_with):
        session = page_with(LINKS)
        rows = session.query_all("a", extract={"href": "@href"})
        assert [r["href"] for r in rows] == ["/one", "/two", "/nested"]

    def test_a_sub_selector_equal_to_the_outer_one_finds_nothing(self, page_with):
        # THE bug. "a@href" against outer selector "a" asks for an <a> nested
        # INSIDE each <a>, which never exists — so every link came back None
        # and apply-link discovery silently found nothing, everywhere.
        session = page_with(LINKS)
        rows = session.query_all("a", extract={"href": "a@href"})
        assert [r["href"] for r in rows] == [None, None, None]

    def test_a_genuinely_nested_sub_selector_still_works(self, page_with):
        # The same syntax IS correct when the sub-element really is nested —
        # which is why the trap is easy to miss in review.
        session = page_with(LINKS)
        rows = session.query_all(".card", extract={"href": "a@href"})
        assert [r["href"] for r in rows] == ["/nested"]

    def test_an_empty_sub_selector_reads_the_elements_text(self, page_with):
        session = page_with(LINKS)
        rows = session.query_all("a", extract={"text": ""})
        assert [r["text"] for r in rows] == ["One", "Two", "Nested"]

    def test_a_missing_attribute_is_none_rather_than_an_empty_string(self, page_with):
        # None means "not present"; "" means "present and empty". Collapsing
        # them loses the only signal that a selector is wrong.
        session = page_with('<a href="/x">X</a>')
        rows = session.query_all("a", extract={"target": "@target"})
        assert rows[0]["target"] is None


class TestNumericElementIds:
    """``#4001209002`` is legal HTML and INVALID CSS."""

    NUMERIC = '<input id="4001209002" type="text"><input id="normal" type="text">'

    def test_the_hash_form_of_a_numeric_id_is_rejected_by_the_browser(self, page_with):
        # Documents WHY the attribute form is used everywhere. Greenhouse
        # really does emit ids like this, and "#4001209002" threw and killed
        # whole autopilot cycles.
        session = page_with(self.NUMERIC)
        # Playwright surfaces the invalid-selector error as its own type; what
        # matters is that the browser refuses it rather than silently missing.
        with pytest.raises(Exception, match=r"(?i)selector|syntax|expected"):
            session.fill("#4001209002", "value")

    def test_the_attribute_form_works(self, page_with):
        session = page_with(self.NUMERIC)
        session.fill('[id="4001209002"]', "value")
        assert session.input_value('[id="4001209002"]') == "value"

    def test_detect_fields_always_emits_the_attribute_form(self, page_with):
        session = page_with(self.NUMERIC)
        selectors = [row["selector"] for row in session.detect_fields()]
        assert all(s.startswith('[id="') for s in selectors), selectors
        # And every one of them is actually usable.
        for selector in selectors:
            session.fill(selector, "x")


class TestDetectFieldsLabelResolution:
    def test_a_label_for_a_numeric_id_is_still_found(self, page_with):
        # The label lookup builds a selector from the id too, so it hit the
        # same invalid-CSS trap and silently lost the question text.
        session = page_with(
            '<label for="4001209002">LinkedIn Profile</label><input id="4001209002" type="text">'
        )
        rows = session.detect_fields()
        assert rows[0]["label"] == "LinkedIn Profile"

    def test_a_wrapping_label_is_found(self, page_with):
        session = page_with("<label>Given Name<input type='text' id='gn'></label>")
        assert session.detect_fields()[0]["label"].startswith("Given Name")

    def test_a_label_on_the_field_wrapper_is_found(self, page_with):
        # React form libraries put the <label> several levels above the input.
        session = page_with(
            "<div><label>Current Employer</label><div><div>"
            "<input type='text' id='ce'></div></div></div>"
        )
        assert session.detect_fields()[0]["label"] == "Current Employer"

    def test_hidden_fields_are_not_reported_as_fillable(self, page_with):
        session = page_with(
            "<input type='hidden' id='csrf'><input type='text' id='real'>"
            "<input type='text' id='gone' style='display:none'>"
        )
        ids = [row["id_attr"] for row in session.detect_fields()]
        assert ids == ["real"]


class TestDetectButtons:
    def test_an_upload_button_beside_a_file_input_is_flagged(self, page_with):
        session = page_with(
            "<form><div class='w'><input type='file' id='cv'>"
            "<button type='submit' id='up'>Upload file</button></div>"
            "<button type='submit' id='go'>Submit Application</button></form>"
        )
        rows = {r["selector"]: r for r in session.detect_buttons()}
        assert rows['[id="up"]']["near_file_input"] is True
        # And the real submit button is NOT, even though it shares the form.
        assert rows['[id="go"]']["near_file_input"] is False

    def test_sharing_a_form_with_a_file_input_is_not_a_file_widget(self, page_with):
        # A one-column form: the button and the CV field share a parent within
        # two hops. Treating that as an upload widget classified "Apply for
        # this job" as an upload control and lost the form entirely.
        session = page_with(
            "<form><input type='text' id='a'><input type='text' id='b'>"
            "<input type='file' id='cv'><button type='submit' id='go'>"
            "Apply for this job</button></form>"
        )
        rows = {r["selector"]: r for r in session.detect_buttons()}
        assert rows['[id="go"]']["near_file_input"] is False

    def test_a_hidden_button_is_not_offered_as_a_submit_target(self, page_with):
        session = page_with(
            "<button id='hidden' style='display:none'>Submit Application</button>"
            "<button id='shown'>Submit Application</button>"
        )
        selectors = [r["selector"] for r in session.detect_buttons()]
        assert selectors == ['[id="shown"]']

    def test_the_accessible_name_wins_over_visible_text(self, page_with):
        session = page_with("<button id='b' aria-label='Submit Application'>→</button>")
        assert session.detect_buttons()[0]["accessible_name"] == "Submit Application"


class TestLabelsDoNotSwallowTheirOwnControl:
    """A label that WRAPS its control also contains that control's text.

    For a <select> that is every option, so the question came out as
    "genderselect ...malefemaledecline to self-identify" — unreadable to a
    human and unanswerable by a model. Observed live on Lever, 2026-08-31.
    """

    def test_a_wrapping_label_around_a_select_reads_as_the_question_only(self, page_with):
        session = page_with(
            "<label>Gender"
            "<select id='g'><option>Male</option><option>Female</option>"
            "<option>Decline to self-identify</option></select>"
            "</label>"
        )
        row = next(r for r in session.detect_fields() if r["id_attr"] == "g")
        assert row["label"] == "Gender"
        assert "male" not in row["label"].lower()

    def test_a_wrapping_label_around_a_text_input_is_unaffected(self, page_with):
        session = page_with("<label>Given Name<input type='text' id='gn'></label>")
        row = next(r for r in session.detect_fields() if r["id_attr"] == "gn")
        assert row["label"] == "Given Name"

    def test_a_label_containing_a_button_drops_the_button_text(self, page_with):
        session = page_with(
            "<label>Upload your CV<button>Choose file</button><input type='file' id='cv'></label>"
        )
        row = next(r for r in session.detect_fields() if r["id_attr"] == "cv")
        assert row["label"] == "Upload your CV"

    def test_the_options_are_still_reported_separately(self, page_with):
        # Stripped from the LABEL, not lost — the answerer needs them.
        session = page_with(
            "<label>Gender<select id='g'><option>Male</option>"
            "<option>Female</option></select></label>"
        )
        row = next(r for r in session.detect_fields() if r["id_attr"] == "g")
        assert row["options"] == ["Male", "Female"]
