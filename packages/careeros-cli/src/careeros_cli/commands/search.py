"""`careeros search` command: run one JobAgent discovery + qualification cycle."""

from __future__ import annotations

import argparse

from careeros_cli.context import CLIContext, build_context
from careeros_job_agent import CycleSummary
from careeros_job_providers import JobSearchQuery


def run_search(context: CLIContext, identity_id: str, query: JobSearchQuery) -> CycleSummary:
    return context.agent.run_cycle(identity_id, query)


def cmd_search(args: argparse.Namespace) -> int:
    context = build_context(args.data_dir)
    query = JobSearchQuery(
        keywords=args.keywords or [], remote_only=args.remote_only, limit=args.limit
    )
    summary = run_search(context, args.identity_id, query)
    print(summary.model_dump_json())
    return 0
