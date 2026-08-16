"""Fills and submits a live browser form from an ApplicationPackage +
FormFieldMapping.
"""

from __future__ import annotations

from careeros_application_engine import ApplicationPackage
from careeros_application_runner.models import FormFieldMapping
from careeros_browser import BrowserSession


def fill_application_form(
    session: BrowserSession,
    package: ApplicationPackage,
    mapping: FormFieldMapping,
    *,
    resume_file_path: str | None = None,
) -> None:
    content = package.resume_content
    if mapping.first_name_selector or mapping.last_name_selector:
        first_name, _, last_name = content.full_name.partition(" ")
        if mapping.first_name_selector:
            session.fill(mapping.first_name_selector, first_name)
        if mapping.last_name_selector and last_name:
            session.fill(mapping.last_name_selector, last_name)
    elif mapping.full_name_selector:
        session.fill(mapping.full_name_selector, content.full_name)
    if mapping.email_selector:
        session.fill(mapping.email_selector, content.email)
    if mapping.phone_selector and content.phone:
        session.fill(mapping.phone_selector, content.phone)
    if mapping.resume_upload_selector and resume_file_path:
        session.upload_file(mapping.resume_upload_selector, resume_file_path)
    if mapping.cover_letter_selector:
        session.fill(mapping.cover_letter_selector, package.cover_letter)


def submit_application_form(session: BrowserSession, mapping: FormFieldMapping) -> None:
    session.click(mapping.submit_selector)
