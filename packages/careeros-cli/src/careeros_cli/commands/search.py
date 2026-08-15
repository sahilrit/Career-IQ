"""`careeros search` command: run one JobAgent discovery + qualification cycle."""

from __future__ import annotations

import argparse
import json

from careeros_cli.context import CLIContext, build_context
from careeros_job_providers import JobSearchQuery


def run_search(context: CLIContext, identity_id: str, query: JobSearchQuery) -> dict[str, int]:
    return context.agent.run_cycle(identity_id, query)


def cmd_search(args: argparse.Namespace) -> int:
    context = build_context(args.data_dir)
    query = JobSearchQuery(
        keywords=args.keywords or [], remote_only=args.remote_only, limit=args.limit
    )
    summary = run_search(context, args.identity_id, query)
    print(json.dumps(summary))
    return 0
