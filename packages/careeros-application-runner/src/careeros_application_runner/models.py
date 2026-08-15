"""Form field mapping: per-site selectors mapped to standard field purposes.

Every job site's application form has a different DOM, so nothing in
this package hardcodes selectors for a specific site — a
``FormFieldMapping`` supplies them (typically from a per-site
plugin/config), and everything else here is site-agnostic.
"""

from __future__ import annotations

from pydantic import BaseModel


class FormFieldMapping(BaseModel):
    full_name_selector: str | None = None
    email_selector: str | None = None
    phone_selector: str | None = None
    resume_upload_selector: str | None = None
    cover_letter_selector: str | None = None
    submit_selector: str
    success_selector: str
