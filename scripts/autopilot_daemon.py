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
import os
import time
from typing import Any

from careeros_application_engine import TemplateCoverLetterGenerator
from careeros_arbeitnow_provider import ArbeitnowProvider
from careeros_ashby_provider import AshbyProvider
from careeros_autopilot import run_autopilot_cycle
from careeros_common import DocumentStore, open_store
from careeros_greenhouse_provider import GreenhouseProvider
from careeros_himalayas_provider import HimalayasProvider
from careeros_himalayas_provider.client import HttpxHimalayasTransport
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
    "meta ads,facebook ads,growth marketing,digital marketing,marketing manager,"
    "marketing specialist,ecommerce,shopify,conversion rate,cro"
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

    while True:
        try:
            report = run_autopilot_cycle(
                scoped,
                provider_registry=build_registry(),
                keywords=keywords,
                headless=not arguments.show_browser,
                cover_letter_generator=cover_letter_generator,
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
