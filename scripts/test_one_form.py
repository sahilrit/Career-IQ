"""Prove the autopilot can fill ONE real application form — end to end, in a
visible browser, with a loud play-by-play so we can see EXACTLY where it
stops if it stops.

This is a diagnostic, NOT the daemon: it touches a single Greenhouse form,
fills every field it can, screenshots it, and pauses (never submits). The
whole point is that the terminal output tells you what happened:

    * "no form detected on the page"        -> the form never loaded / not a form
    * "form detected: email=... fields=0"   -> found the form but no questions
    * "FILLED: [id=...] = 'Sahil'"           -> it's actually filling

Usage (against your LIVE account):
    export CAREEROS_DATABASE_URL="postgres://…external…"
    # optional: better answers for custom questions
    export CAREEROS_AI_KEY="gsk_…or…AIza…"
    uv run python scripts/test_one_form.py --workspace-id 72c51f62-10b3-4017-9884-99707ab6b8e9
    # or target one specific Greenhouse posting yourself:
    uv run python scripts/test_one_form.py --workspace-id <ID> --url https://boards.greenhouse.io/…
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from careeros_application_engine import QuestionAnswerer, build_application_package
from careeros_application_runner import fill_application_form
from careeros_ats_providers import ADAPTER_CLASSES, AtsBoardProvider, greenhouse_boards
from careeros_autopilot.page_analysis import detect_form_mapping, prepare_application_page
from careeros_autopilot.resume_file import write_resume_pdf
from careeros_browser import launch_browser_session
from careeros_career_brain import CareerBrainRepository
from careeros_common import DocumentStore, open_store
from careeros_job_providers import JobPosting, JobSearchQuery
from careeros_tenancy import TenantScopedDocumentStore

DEFAULT_KEYWORDS = (
    "performance marketing,growth marketing,growth,digital marketing,marketing manager,"
    "product marketing,paid social,paid media,demand generation,marketing"
)


def _load_brain(store: Any, workspace_id: str) -> Any:
    scoped = TenantScopedDocumentStore(store, workspace_id)
    repository = CareerBrainRepository(scoped)
    brains = repository.list_all()
    if not brains:
        raise SystemExit(
            f"No Career Brain in workspace {workspace_id}. "
            "Check CAREEROS_DATABASE_URL and the workspace id."
        )
    return brains[0]


def _pick_greenhouse_posting(keywords: list[str]) -> JobPosting | None:
    print("Searching Greenhouse for a job to test on…")
    result = AtsBoardProvider(ADAPTER_CLASSES["greenhouse"](), greenhouse_boards()).search(
        JobSearchQuery(keywords=keywords, remote_only=False, limit=200)
    )
    greenhouse = [posting for posting in result.postings if "greenhouse.io" in (posting.url or "")]
    print(
        f"  Greenhouse returned {len(result.postings)} postings "
        f"({len(greenhouse)} on greenhouse.io)."
    )
    return greenhouse[0] if greenhouse else (result.postings[0] if result.postings else None)


def _ai_client() -> Any | None:
    key = os.environ.get("CAREEROS_AI_KEY", "").strip()
    if not key:
        return None
    try:
        # Through the gateway, not a raw vendor client: a key that is expired
        # or rate-limited then falls back to a locally authenticated CLI
        # instead of turning AI answers off for the whole run.
        from careeros_llm import GatewayAIClient, LLMGateway, LLMTask

        model = os.environ.get("CAREEROS_AI_MODEL", "").strip() or None
        return GatewayAIClient(LLMGateway.from_env(api_key=key, api_model=model), LLMTask.ANSWER)
    except Exception as error:
        print(f"  (AI answers off: {type(error).__name__}: {error})")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--url", default=None, help="a specific Greenhouse posting URL to test")
    parser.add_argument("--keywords", default=DEFAULT_KEYWORDS)
    parser.add_argument("--data-dir", default=".careeros/data")
    args = parser.parse_args()

    if os.environ.get("CAREEROS_DATABASE_URL", "").strip():
        store = open_store()
        print(f"Store: Postgres (live) — workspace {args.workspace_id}")
    else:
        store = DocumentStore(f"{args.data_dir}/careeros.db")
        print(f"Store: local SQLite {args.data_dir}/careeros.db")

    brain = _load_brain(store, args.workspace_id)
    print(f"Career Brain: {brain.identity.full_name} <{brain.identity.email}>")

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    if args.url:
        posting = JobPosting(
            source_provider="greenhouse",
            external_id="manual",
            title="Test posting",
            company_name="(from URL)",
            url=args.url,
            remote=True,
        )
        print(f"Testing the URL you gave: {args.url}")
    else:
        posting = _pick_greenhouse_posting(keywords)
        if posting is None:
            raise SystemExit("No Greenhouse posting found to test on. Try passing --url.")
        print(f"Testing: {posting.title} @ {posting.company_name}\n  {posting.url}")

    # A résumé PDF for the upload field.
    resume_path: str | None = None
    try:
        package = build_application_package(brain, posting)
        resume_path = str(write_resume_pdf(package.resume_text, Path(".careeros/test/resume.pdf")))
        print(f"Résumé PDF ready: {resume_path}")
    except Exception as error:
        print(f"  (résumé PDF skipped: {type(error).__name__}: {error})")
        package = build_application_package(brain, posting)

    print("\nOpening a VISIBLE browser — watch it work…\n")
    with launch_browser_session(headless=False) as session:
        error = prepare_application_page(session, posting)
        print(f"Page loaded. current_url = {session.current_url}")
        if error is not None:
            print(f"STOP: could not reach a form — {error}")
            input("\n(press Enter to close the browser) ")
            return

        # How much is even on the page? (diagnoses 'no form' vs 'form, no fields'.)
        for selector in ("input", "select", "textarea", "[role='combobox']"):
            try:
                count = len(session.query_all(selector, extract={"id": "@id"}))
            except Exception:
                count = -1
            print(f"  page has {count:>3} <{selector}> elements")

        mapping = detect_form_mapping(session, require_submit=False)
        if mapping is None:
            print("\nSTOP: no fillable form detected (no email field found).")
            session.screenshot(Path(".careeros/test/no-form.png"))
            print("  screenshot: .careeros/test/no-form.png")
            input("\n(press Enter to close the browser) ")
            return

        print("\nFORM DETECTED:")
        print(f"  email      : {mapping.email_selector}")
        print(f"  first/last : {mapping.first_name_selector} / {mapping.last_name_selector}")
        print(f"  full name  : {mapping.full_name_selector}")
        print(f"  phone      : {mapping.phone_selector}")
        print(f"  résumé     : {mapping.resume_upload_selector}")
        print(f"  cover      : {mapping.cover_letter_selector}")
        print(f"  questions  : {len(mapping.question_fields)}")
        for field in mapping.question_fields:
            print(f"      - [{field.kind}] {field.question!r}  ({field.selector})")

        # Answer the custom questions from the brain (+ optional AI).
        answerer = QuestionAnswerer(brain, posting, ai_client=_ai_client())
        answers: dict[str, str] = {}
        for field in mapping.question_fields:
            answer = answerer.answer(field.question)
            if answer.answerable and answer.text:
                answers[field.selector] = answer.text
                print(f"  answer -> {field.question!r} = {answer.text!r}")
            else:
                print(f"  answer -> {field.question!r} = (left blank — no truthful answer)")

        print("\nFilling the form now (no submit)…")
        fill_application_form(
            session, package, mapping, resume_file_path=resume_path, question_answers=answers
        )

        shot = session.screenshot(Path(".careeros/test/filled.png"))
        print(f"\nDONE. Screenshot of the filled form: {shot}")
        print("Look at the browser: the fields should be filled. Nothing was submitted.")
        input("\n(press Enter to close the browser) ")


if __name__ == "__main__":
    main()
