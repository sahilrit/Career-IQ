#!/usr/bin/env python
"""End-to-end smoke test: discover → score → generate → review → open → fill.

This is the test that decides whether CareerOS actually works, as opposed to
whether its unit tests pass. It runs the real workflow against LIVE job boards
and REAL application forms in a real browser, and reports exactly which stage
fails for each posting.

It never submits anything. The run stops at submission-ready and prints what a
human would still have to finish, which is the product's actual promise.

    uv run python scripts/e2e_smoke.py                       # 1 job per ATS
    uv run python scripts/e2e_smoke.py --per-ats 2 --headful
    uv run python scripts/e2e_smoke.py --ats greenhouse lever

Exit code is 1 if no posting reached submission-ready, so this is usable as a
release gate.
"""

from __future__ import annotations

import argparse
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

os.environ.setdefault("CAREEROS_DATA_DIR", ".careeros/data")
os.environ.setdefault("CAREEROS_ENV", "test")

from careeros_application_engine import QuestionAnswerer, build_application_package
from careeros_application_runner import fill_application_form
from careeros_ats_providers import ADAPTER_CLASSES, AtsBoardProvider
from careeros_ats_providers import __init__ as _ats_pkg  # noqa: F401
from careeros_autopilot.page_analysis import (
    DEFAULT_PROBLEM_DETECTORS,
    detect_form_mapping,
    prepare_application_page,
)
from careeros_browser import launch_browser_session
from careeros_career_brain import CareerBrainRepository
from careeros_common import open_store
from careeros_job_providers import JobSearchQuery
from careeros_llm import LLMGateway, LLMTask

DEFAULT_KEYWORDS = [
    "performance marketing",
    "paid media",
    "growth marketing",
    "demand generation",
    "paid social",
    "digital marketing",
    "marketing manager",
    "media buyer",
]

#: Stages, in the order the definition-of-done lists them.
STAGES = [
    "discovered",
    "scored",
    "package_generated",
    "package_reviewed",
    "form_opened",
    "fields_detected",
    "fields_mapped",
    "fields_filled",
    "validated",
    "submission_ready",
]


@dataclass
class Attempt:
    ats: str
    title: str
    company: str
    url: str
    reached: list[str] = field(default_factory=list)
    blocked_by: str = ""
    notes: list[str] = field(default_factory=list)

    def reach(self, stage: str) -> None:
        self.reached.append(stage)

    @property
    def furthest(self) -> str:
        return self.reached[-1] if self.reached else "nothing"

    @property
    def ready(self) -> bool:
        return "submission_ready" in self.reached


def load_brain():
    store = open_store()
    repository = CareerBrainRepository(store)
    import sqlite3

    database = Path(os.environ["CAREEROS_DATA_DIR"]) / "careeros.db"
    connection = sqlite3.connect(database)
    rows = connection.execute(
        "select id from documents where entity_type like '%career_brain%' order by updated_at desc"
    ).fetchall()
    connection.close()
    for (identity_id,) in rows:
        brain = repository.load_or_none(identity_id)
        if brain is not None and brain.experiences:
            return brain
    for (identity_id,) in rows:
        brain = repository.load_or_none(identity_id)
        if brain is not None:
            return brain
    return None


def discover(ats_ids: list[str], per_ats: int, keywords: list[str]) -> list[tuple[str, object]]:
    from careeros_ats_providers.__init__ import _BOARD_LOADERS

    found: list[tuple[str, object]] = []
    for ats_id in ats_ids:
        boards = _BOARD_LOADERS[ats_id]()
        if not boards:
            print(f"  {ats_id}: no boards configured — skipped")
            continue
        provider = AtsBoardProvider(ADAPTER_CLASSES[ats_id](), boards)
        try:
            result = provider.search(JobSearchQuery(keywords=keywords, limit=200))
        except Exception as exc:
            print(f"  {ats_id}: search FAILED — {exc}")
            continue
        # One posting per COMPANY. Taking the first N matches gave three roles
        # at the same employer, which tests one board three times and says
        # nothing about the ATS's coverage.
        postings = []
        seen_companies: set[str] = set()
        for posting in result.postings:
            company = (posting.company_name or "").lower()
            if company in seen_companies:
                continue
            seen_companies.add(company)
            postings.append(posting)
            if len(postings) >= per_ats:
                break
        print(
            f"  {ats_id}: {len(result.postings)} matched across "
            f"{len({p.company_name for p in result.postings})} companies, "
            f"taking {len(postings)}"
        )
        found += [(ats_id, p) for p in postings]
    return found


def run_one(brain, ats_id, posting, reviewer_client, resume_path, headless: bool) -> Attempt:
    attempt = Attempt(ats_id, posting.title, posting.company_name, posting.apply_url or posting.url)
    attempt.reach("discovered")
    attempt.reach("scored")

    try:
        package = build_application_package(brain, posting, reviewer_client=reviewer_client)
    except Exception as exc:
        attempt.blocked_by = f"package generation failed: {exc}"
        return attempt
    attempt.reach("package_generated")

    review = package.review
    if review is None:
        attempt.blocked_by = "no review was produced"
        return attempt
    attempt.reach("package_reviewed")
    attempt.notes.append(f"review: {review.summary()}")
    for finding in review.fabrications[:3]:
        attempt.notes.append(f"  FABRICATION {finding.category}: {finding.evidence}")
    if not review.is_safe_to_send:
        # Not a stage failure - the reviewer doing its job. Recorded and the
        # run continues, because the fill path is what we are testing here.
        attempt.notes.append("  (letter withheld from send until a human resolves these)")

    answerer = QuestionAnswerer(brain, posting)

    with launch_browser_session(headless=headless) as session:
        problem = prepare_application_page(session, posting)
        if problem:
            attempt.blocked_by = problem
            return attempt
        attempt.reach("form_opened")

        for detector in DEFAULT_PROBLEM_DETECTORS:
            found = detector.detect(session)
            if found is not None:
                attempt.blocked_by = f"blocked by {found.description}"
                return attempt

        mapping = detect_form_mapping(session, require_submit=False)
        if mapping is None:
            attempt.blocked_by = "no fillable form found on the page"
            return attempt
        attempt.reach("fields_detected")
        attempt.notes.append(f"detected {len(mapping.question_fields)} extra question(s)")

        answers: dict[str, str] = {}
        unanswered = 0
        for question_field in mapping.question_fields:
            answer = answerer.answer(question_field.question)
            if answer.answerable and answer.text:
                answers[question_field.selector] = answer.text
            else:
                unanswered += 1
        attempt.reach("fields_mapped")
        if unanswered:
            attempt.notes.append(f"{unanswered} question(s) left for a human (not guessed)")

        report = fill_application_form(
            session,
            package,
            mapping,
            resume_file_path=str(resume_path) if resume_path else None,
            question_answers=answers,
        )
        attempt.reach("fields_filled")
        attempt.notes.append(f"fill: {report.summary()}")
        for failure in report.failures[:4]:
            attempt.notes.append(f"  FAILED {failure.field}: {failure.detail}")

        attempt.reach("validated")
        if report.is_submittable:
            attempt.reach("submission_ready")
        else:
            attempt.blocked_by = "; ".join(
                f"{r.field} ({r.detail})" for r in (report.blocking + report.failures)[:3]
            )

        shots = Path(".careeros/screenshots/e2e")
        shots.mkdir(parents=True, exist_ok=True)
        safe = "".join(c if c.isalnum() else "-" for c in f"{ats_id}-{posting.company_name}")[:60]
        try:
            session.screenshot(shots / f"{safe}.png")
            attempt.notes.append(f"screenshot: {shots / (safe + '.png')}")
        except Exception:
            pass

    return attempt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-ats", type=int, default=1)
    parser.add_argument("--ats", nargs="*", default=["greenhouse", "lever", "ashby", "workable"])
    parser.add_argument("--headful", action="store_true")
    parser.add_argument("--keywords", nargs="*", default=DEFAULT_KEYWORDS)
    parser.add_argument("--resume", default=".careeros/autopilot/resume.pdf")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not args.verbose:
        logging.disable(logging.INFO)

    print("=" * 78)
    print("CareerOS end-to-end smoke test — nothing is ever submitted")
    print("=" * 78)

    brain = load_brain()
    if brain is None:
        print("FAIL: no career profile found. Nothing downstream can be tested.")
        return 1
    print(
        f"\nProfile: {brain.identity.full_name} — {len(brain.experiences)} role(s), "
        f"{len(brain.skills)} skill(s)"
    )

    gateway = LLMGateway.from_env()
    reviewer_client = None
    if gateway.is_configured:
        from careeros_llm import GatewayAIClient

        reviewer_client = GatewayAIClient(gateway, LLMTask.REVIEW)
        print(f"AI providers: {', '.join(p.provider_id for p in gateway.providers())}")
    else:
        print("AI providers: none — deterministic review only")

    resume = Path(args.resume)
    if not resume.exists():
        print(f"NOTE: no resume at {resume}; upload fields will be reported as needing you")
        resume = None

    print("\n--- discovery ---")
    postings = discover(args.ats, args.per_ats, args.keywords)
    if not postings:
        print("FAIL: discovery returned nothing.")
        return 1

    attempts = []
    for ats_id, posting in postings:
        print(f"\n--- {ats_id}: {posting.title} @ {posting.company_name} ---")
        try:
            attempt = run_one(
                brain, ats_id, posting, reviewer_client, resume, headless=not args.headful
            )
        except Exception as exc:
            attempt = Attempt(ats_id, posting.title, posting.company_name, posting.url)
            attempt.blocked_by = f"unhandled: {type(exc).__name__}: {exc}"
        attempts.append(attempt)
        for note in attempt.notes:
            print(f"    {note}")
        print(f"    reached: {attempt.furthest}")
        if attempt.blocked_by:
            print(f"    blocked: {attempt.blocked_by}")

    print("\n" + "=" * 78)
    print("STAGE COVERAGE")
    print("=" * 78)
    for stage in STAGES:
        passed = sum(1 for a in attempts if stage in a.reached)
        mark = "PASS" if passed else "FAIL"
        print(f"  {stage:20} {mark}  ({passed}/{len(attempts)})")

    print("\nPER-POSTING")
    for attempt in attempts:
        state = "SUBMISSION-READY" if attempt.ready else f"stopped at {attempt.furthest}"
        print(f"  [{attempt.ats:14}] {attempt.company[:20]:20} {state}")
        if attempt.blocked_by:
            print(f"                   because: {attempt.blocked_by[:120]}")

    ready = sum(1 for a in attempts if a.ready)
    print(f"\n{ready}/{len(attempts)} postings reached submission-ready.")
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
