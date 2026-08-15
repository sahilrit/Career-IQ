"""`careeros applications` command: list an identity's applications."""

from __future__ import annotations

import argparse
import sys

from careeros_career_brain import Application
from careeros_cli.context import build_context


def filter_applications(applications: list[Application], status: str | None) -> list[Application]:
    if status is None:
        return applications
    return [a for a in applications if a.status.value == status]


def format_applications(applications: list[Application]) -> str:
    lines = []
    for app in applications:
        score = f"{app.match_score:.2f}" if app.match_score is not None else "-"
        lines.append(
            f"{app.id}  {app.status.value:<12}  score={score}  {app.job_title} @ {app.company_name}"
        )
    return "\n".join(lines)


def cmd_list(args: argparse.Namespace) -> int:
    context = build_context(args.data_dir)
    brain = context.repository.load_or_none(args.identity_id)
    if brain is None:
        print(f"No Career Brain found with id {args.identity_id!r}", file=sys.stderr)
        return 1
    applications = filter_applications(brain.applications, args.status)
    print(format_applications(applications))
    return 0
