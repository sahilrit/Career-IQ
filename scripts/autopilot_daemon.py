"""Run the CareerOS autopilot continuously: every N hours, discover new
jobs, qualify them against the Career Brain, and autonomously submit
applications — captchas and login walls are handed off, never bypassed.

Usage (apply against your LIVE account):
    export CAREEROS_DATABASE_URL="postgres://…"   # Render → API service → the
                                                  # database's *External* URL
    uv run playwright install chromium            # one-time browser install
    uv run python scripts/autopilot_daemon.py --workspace-id <ID> --once
        [--keywords "performance marketing,ppc,..."] \
        [--interval-hours 6] [--show-browser]

Without CAREEROS_DATABASE_URL it runs against a local SQLite file (offline
testing). Every cycle's outcomes are visible on the app's Autopilot page.
Captchas and login walls are handed off, never bypassed — so it submits to
the open ATS forms (Greenhouse/Ashby/Lever) and holds the rest.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import time
from datetime import UTC, datetime
from typing import Any

from careeros_adzuna_provider import AdzunaProvider
from careeros_application_engine import TemplateCoverLetterGenerator
from careeros_arbeitnow_provider import ArbeitnowProvider
from careeros_ashby_provider import AshbyProvider
from careeros_autopilot import run_autopilot_cycle
from careeros_common import DocumentStore, open_store
from careeros_greenhouse_provider import GreenhouseProvider
from careeros_himalayas_provider import HimalayasProvider
from careeros_himalayas_provider.client import HttpxHimalayasTransport
from careeros_hiringcafe_provider import HiringCafeProvider
from careeros_job_providers import JobProviderRegistry
from careeros_jobicy_provider import JobicyProvider
from careeros_lever_provider import LeverProvider
from careeros_remoteok_provider import RemoteOKProvider
from careeros_tenancy import TenantScopedDocumentStore
from careeros_themuse_provider import TheMuseProvider
from careeros_weworkremotely_provider import WeWorkRemotelyProvider
from careeros_workingnomads_provider import WorkingNomadsProvider

DEFAULT_KEYWORDS = (
    "performance marketing,media buyer,paid social,paid media,paid search,ppc,"
    "meta ads,facebook ads,google ads,growth marketing,growth,demand generation,"
    "digital marketing,marketing manager,marketing specialist,marketing analyst,"
    "product marketing,brand marketing,content marketing,lifecycle marketing,"
    "email marketing,crm,marketing automation,seo,sem,social media,"
    "user acquisition,paid acquisition,retention marketing,affiliate marketing,"
    "ecommerce,shopify,conversion rate,cro"
)


def build_registry() -> JobProviderRegistry:
    registry = JobProviderRegistry()
    registry.register(RemoteOKProvider())
    registry.register(ArbeitnowProvider())
    registry.register(HimalayasProvider(HttpxHimalayasTransport(max_entries=1000)))
    registry.register(JobicyProvider())
    registry.register(WorkingNomadsProvider())
    registry.register(WeWorkRemotelyProvider())
    registry.register(TheMuseProvider())
    # Open-form ATS boards: forms the autopilot can actually submit to.
    registry.register(GreenhouseProvider())
    registry.register(AshbyProvider())
    registry.register(LeverProvider())
    # HiringCafe: keyless; each posting's url is the employer's direct apply
    # link. Adzuna: needs ADZUNA_APP_ID / ADZUNA_APP_KEY in the environment —
    # without them it reports unavailable and is skipped, so it's safe to add.
    registry.register(HiringCafeProvider())
    registry.register(AdzunaProvider())
    return registry


class _ResilientCoverLetter:
    """AI cover letters, but any provider error (rate limit, bad key, outage)
    falls back to the template so one flaky call never breaks a whole cycle."""

    def __init__(self, ai: Any, fallback: Any) -> None:
        self._ai = ai
        self._fallback = fallback

    def generate(self, brain: Any, posting: Any) -> str:
        try:
            return self._ai.generate(brain, posting)
        except Exception as error:
            print(f"    (AI cover letter failed: {type(error).__name__}; used template)")
            return self._fallback.generate(brain, posting)


def resolve_cover_letter_generator(scoped: Any, workspace_id: str) -> Any | None:
    """The workspace's AI cover-letter writer (Gemini/Anthropic/…), wrapped so
    failures fall back to templates. None when there's no key or it can't be
    decrypted (then the cycle uses templates).

    Simplest path: set CAREEROS_AI_KEY (your Gemini AIza… key) and we use it
    directly — no vault, no CAREEROS_SECRET_KEY juggling. Otherwise we read the
    key the live app stored, which needs CAREEROS_SECRET_KEY here to MATCH the
    value the live app encrypted it with.
    """
    direct_key = os.environ.get("CAREEROS_AI_KEY", "").strip()
    if direct_key:
        try:
            from careeros_ai import build_client
            from careeros_application_engine import AICoverLetterGenerator

            model = os.environ.get("CAREEROS_AI_MODEL", "").strip() or None
            ai_generator = AICoverLetterGenerator(build_client(direct_key, model))
        except Exception as error:
            print(f"AI cover letters: off ({type(error).__name__}: {error}) — using templates")
            return None
        print("AI cover letters: ON (CAREEROS_AI_KEY) — written by your AI model")
        return _ResilientCoverLetter(ai_generator, TemplateCoverLetterGenerator())

    try:
        from careeros_api import ai_support

        ai_generator = ai_support.resolve_cover_letter_generator(scoped, workspace_id)
    except Exception as error:
        print(f"AI cover letters: off ({type(error).__name__}: {error}) — using templates")
        return None
    if ai_generator is None:
        print("AI cover letters: off (no AI key stored for this workspace) — using templates")
        return None
    print("AI cover letters: ON — each application is written by your AI model")
    return _ResilientCoverLetter(ai_generator, TemplateCoverLetterGenerator())


def resolve_question_ai_client(scoped: Any, workspace_id: str) -> Any | None:
    """Raw AI client for answering custom form questions. CAREEROS_AI_KEY wins;
    otherwise the workspace's stored key. None (rules-only) on any failure."""
    direct_key = os.environ.get("CAREEROS_AI_KEY", "").strip()
    if direct_key:
        try:
            from careeros_ai import build_client

            model = os.environ.get("CAREEROS_AI_MODEL", "").strip() or None
            return build_client(direct_key, model)
        except Exception:
            return None
    try:
        from careeros_api import ai_support

        return ai_support.resolve_ai_client(scoped, workspace_id)
    except Exception:
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--data-dir", default=".careeros/data")
    parser.add_argument("--keywords", default=DEFAULT_KEYWORDS)
    parser.add_argument("--interval-hours", type=float, default=6.0)
    parser.add_argument("--once", action="store_true", help="run one cycle and exit")
    parser.add_argument(
        "--show-browser", action="store_true", help="run the browser visibly instead of headless"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="reach and map each form but never click submit (safe validation)",
    )
    parser.add_argument(
        "--review",
        action="store_true",
        help="fill each reachable form (incl. captcha-gated) but never submit; "
        "pause on a visible browser so you solve the captcha and click submit",
    )
    parser.add_argument(
        "--assist",
        action="store_true",
        help="fill each form (basics, résumé, cover letter, screening questions) and "
        "pause on a visible browser so you review and click submit, then continue",
    )
    arguments = parser.parse_args()

    keywords = [keyword.strip() for keyword in arguments.keywords.split(",") if keyword.strip()]
    # Apply against the SAME database as the live app: set CAREEROS_DATABASE_URL
    # to your Render Postgres (its *External* connection string) so the daemon
    # sees your real Career Brain and qualified jobs. Without it, fall back to a
    # local SQLite file under --data-dir for offline testing.
    if os.environ.get("CAREEROS_DATABASE_URL", "").strip():
        store = open_store()
        print(f"Store: Postgres (CAREEROS_DATABASE_URL) — workspace {arguments.workspace_id}")
    else:
        store = DocumentStore(f"{arguments.data_dir}/careeros.db")
        print(
            "Store: local SQLite at "
            f"{arguments.data_dir}/careeros.db — set CAREEROS_DATABASE_URL to use your live account"
        )
    scoped = TenantScopedDocumentStore(store, arguments.workspace_id)
    cover_letter_generator = resolve_cover_letter_generator(scoped, arguments.workspace_id)
    question_ai_client = resolve_question_ai_client(scoped, arguments.workspace_id)
    if question_ai_client is not None:
        print("AI form answers: ON — custom questions answered from your profile.")
    if arguments.dry_run:
        print("DRY RUN — will reach and map forms but NEVER submit.")

    def on_prepared(application: Any, posting: Any, package: Any) -> None:
        # Persist to the workspace's review queue so it shows in the web app,
        # then (on a visible browser) pause so the human can finish this one.
        record = {
            "id": application.id,
            "application_id": application.id,
            "job_title": application.job_title,
            "company_name": application.company_name,
            "apply_url": posting.apply_url or posting.url,
            "cover_letter": package.cover_letter,
            "match_score": application.match_score,
            "prepared_at": datetime.now(UTC).isoformat(),
            "status": "pending",
        }
        with contextlib.suppress(Exception):
            scoped.put("prepared_application", application.id, record)
        print("\n" + "=" * 70)
        print(f"✋ READY TO REVIEW: {application.job_title} @ {application.company_name}")
        print(f"   Form: {posting.apply_url or posting.url}")
        print("   Saved to your Review queue in the web app. In the browser window:")
        print("   solve any captcha, check the fields, and click submit to apply.")
        print("=" * 70)
        with contextlib.suppress(EOFError):
            input("   Press Enter for the next one (Ctrl-C to stop)... ")

    review = arguments.review
    assist = arguments.assist and not review  # review wins if both are passed
    if review:
        print("REVIEW MODE — filling forms for you to finish. A browser will open.")
    elif assist:
        print(
            "ASSIST MODE — I fill each form (basics, résumé, cover letter, screening "
            "questions), then pause for you to review and click submit. A browser opens."
        )

    # Both review and assist pause on a visible browser for the human.
    interactive = review or assist

    while True:
        try:
            report = run_autopilot_cycle(
                scoped,
                provider_registry=build_registry(),
                keywords=keywords,
                # Review/assist need a visible browser so you can finish forms.
                headless=(not arguments.show_browser) and not interactive,
                cover_letter_generator=cover_letter_generator,
                submit_enabled=not arguments.dry_run,
                prepare_only=review,
                assist_captcha=assist,
                question_ai_client=question_ai_client,
                on_prepared=on_prepared if interactive else None,
            )
            print(
                f"[{report['ran_at']}] discovered={report['discovered']} "
                f"newly_qualified={report['newly_qualified']} submitted={report['submitted']}"
            )
            for outcome in report["outcomes"]:
                status = "APPLIED" if outcome["submitted"] else "held"
                print(
                    f"    {status:7s} {outcome['job_title']} @ {outcome['company_name']}"
                    + ("" if outcome["submitted"] else f" — {outcome['reason']}")
                )
        except Exception as error:
            print(f"Cycle failed: {type(error).__name__}: {error}")
        if arguments.once:
            break
        time.sleep(arguments.interval_hours * 3600)


if __name__ == "__main__":
    main()
