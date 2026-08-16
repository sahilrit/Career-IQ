"""Run the CareerOS autopilot continuously: every N hours, discover new
jobs, qualify them against the Career Brain, and autonomously submit
applications — captchas and login walls are handed off, never bypassed.

Usage:
    uv run python scripts/autopilot_daemon.py --workspace-id <ID> \
        [--keywords "performance marketing,ppc,..."] \
        [--interval-hours 6] [--once] [--show-browser]

Every cycle's outcomes are visible on the dashboard's Autopilot page.
"""

from __future__ import annotations

import argparse
import time

from careeros_arbeitnow_provider import ArbeitnowProvider
from careeros_autopilot import run_autopilot_cycle
from careeros_common import DocumentStore
from careeros_himalayas_provider import HimalayasProvider
from careeros_himalayas_provider.client import HttpxHimalayasTransport
from careeros_job_providers import JobProviderRegistry
from careeros_remoteok_provider import RemoteOKProvider
from careeros_tenancy import TenantScopedDocumentStore

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
    return registry


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
    store = DocumentStore(f"{arguments.data_dir}/careeros.db")
    scoped = TenantScopedDocumentStore(store, arguments.workspace_id)

    while True:
        try:
            report = run_autopilot_cycle(
                scoped,
                provider_registry=build_registry(),
                keywords=keywords,
                headless=not arguments.show_browser,
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
