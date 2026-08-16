"""Form field mapping: per-site selectors mapped to standard field purposes.

Every job site's application form has a different DOM, so nothing in
this package hardcodes selectors for a specific site — a
``FormFieldMapping`` supplies them (typically from a per-site
plugin/config), and everything else here is site-agnostic.
"""

from __future__ import annotations

from pydantic import BaseModel


class QuestionField(BaseModel):
    """One additional application question on the form: the selector to
    fill/select and the human-readable question label the answerer uses."""

    selector: str
    question: str
    # "text" fills the value; "select" chooses an option by value/label.
    kind: str = "text"


class FormFieldMapping(BaseModel):
    full_name_selector: str | None = None
    # Some ATS forms (e.g. Greenhouse) split the name into two inputs;
    # when these are set they take precedence over full_name_selector.
    first_name_selector: str | None = None
    last_name_selector: str | None = None
    email_selector: str | None = None
    phone_selector: str | None = None
    resume_upload_selector: str | None = None
    cover_letter_selector: str | None = None
    # Additional free-form/screening questions, answered from the Career Brain.
    question_fields: list[QuestionField] = []
    submit_selector: str
    success_selector: str
